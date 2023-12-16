#pragma once
#include <memory>
#include <iostream>
#include <stack>
#include <optional>
#include <mutex>
#include <shared_mutex>
#include <syncstream>
#include <thread>
#include <cmath>
#include <exception>
#include <variant>
#include "ErrorCodes.h"

//#define __CONCURRENT__

template <typename KeyType, typename ValueType, typename CacheType>
class BPlusStore
{
    typedef CacheType::ObjectUIDType ObjectUIDType;
    typedef CacheType::ObjectTypePtr ObjectTypePtr;

private:
    uint32_t m_nDegree;
    std::shared_ptr<CacheType> m_ptrCache;
    std::optional<ObjectUIDType> m_cktRootNodeKey;
    mutable std::shared_mutex mutex;
public:
    ~BPlusStore()
    {
    }

    template<typename... CacheArgs>
    BPlusStore(uint32_t nDegree, CacheArgs... args)
        : m_nDegree(nDegree)
    {    
        m_ptrCache = std::make_shared<CacheType>(args...);
    }

    template <typename DefaultNodeType>
    void init()
    {
        m_cktRootNodeKey = m_ptrCache->template createObjectOfType<DefaultNodeType>();
    }

    template <typename IndexNodeType, typename DataNodeType>
    ErrorCode insert(const KeyType& key, const ValueType& value)
    {
#ifdef __CONCURRENT__
        std::vector<std::unique_lock<std::shared_mutex>> vtLocks;
#endif // __CONCURRENT__

        std::vector<std::pair<ObjectUIDType, ObjectTypePtr>> vtNodes;
        ObjectTypePtr ptrLastNode = nullptr, ptrCurrentNode = nullptr;
        ObjectUIDType ckLastNode, ckCurrentNode;

#ifdef __CONCURRENT__
        vtLocks.push_back(std::unique_lock<std::shared_mutex>(mutex));
#endif // __CONCURRENT__

        ckCurrentNode = m_cktRootNodeKey.value();

        do
        {
            ptrCurrentNode = m_ptrCache->getObject(ckCurrentNode);    //TODO: lock

#ifdef __CONCURRENT__
            vtLocks.push_back(std::unique_lock<std::shared_mutex>(ptrCurrentNode->mutex));
#endif __CONCURRENT__

            if (ptrCurrentNode == nullptr)
            {
                throw new std::exception("should not occur!");   // TODO: critical log.
            }

            if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*ptrCurrentNode->data))
            {
                std::shared_ptr<IndexNodeType> ptrIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*ptrCurrentNode->data);

                if (ptrIndexNode->canTriggerSplit(m_nDegree))
                {
                    vtNodes.push_back(std::pair<ObjectUIDType, ObjectTypePtr>(ckLastNode, ptrLastNode));
                }
                else
                {
#ifdef __CONCURRENT__
                    vtLocks.erase(vtLocks.begin(), vtLocks.begin() + vtLocks.size() - 1);
#endif __CONCURRENT__
                    vtNodes.clear(); //TODO: release locks
                }

                ckLastNode = ckCurrentNode;
                ptrLastNode = ptrCurrentNode;

                ckCurrentNode = ptrIndexNode->getChild(key); // fid it.. there are two kinds of methods..
            }
            else if (std::holds_alternative<std::shared_ptr<DataNodeType>>(*ptrCurrentNode->data))
            {
                std::shared_ptr<DataNodeType> ptrDataNode = std::get<std::shared_ptr<DataNodeType>>(*ptrCurrentNode->data);

                ptrDataNode->insert(key, value);

                if (ptrDataNode->requireSplit(m_nDegree))
                {
                    vtNodes.push_back(std::pair<ObjectUIDType, ObjectTypePtr>(ckLastNode, ptrLastNode));
                    vtNodes.push_back(std::pair<ObjectUIDType, ObjectTypePtr>(ckCurrentNode, ptrCurrentNode));
                }
                else
                {
#ifdef __CONCURRENT__
                    vtLocks.clear();
#endif __CONCURRENT__
                    vtNodes.clear(); //TODO: release locks
                }

                break;
            }
        } while (true);

        KeyType pivotKey;
        ObjectUIDType ckLHSNode;
        std::optional<ObjectUIDType> ckRHSNode;

        while (vtNodes.size() > 0) 
        {
            std::pair<ObjectUIDType, ObjectTypePtr> prNodeDetails = vtNodes.back();

            if (prNodeDetails.second == nullptr)
            {
                if (vtNodes.size() != 1)
                {
                    throw new std::exception("should not occur!");
                }

                m_cktRootNodeKey = m_ptrCache->template createObjectOfType<IndexNodeType>(pivotKey, ckLHSNode, *ckRHSNode);
                break;
            }

            if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*prNodeDetails.second->data))
            {
                std::shared_ptr<IndexNodeType> ptrIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*prNodeDetails.second->data);

                ptrIndexNode->insert(pivotKey, *ckRHSNode);

                ckRHSNode = std::nullopt;

                if (ptrIndexNode->requireSplit(m_nDegree))
                {
                    ErrorCode errCode = ptrIndexNode->template split<std::shared_ptr<CacheType>>(m_ptrCache, ckRHSNode, pivotKey);

                    if (errCode != ErrorCode::Success)
                    {
                        throw new std::exception("should not occur!");
                    }
                }
            }
            else if (std::holds_alternative<std::shared_ptr<DataNodeType>>(*prNodeDetails.second->data))
            {
                std::shared_ptr<DataNodeType> ptrDataNode = std::get<std::shared_ptr<DataNodeType>>(*prNodeDetails.second->data);

                ErrorCode errCode = ptrDataNode->template split<std::shared_ptr<CacheType>, ObjectUIDType>(m_ptrCache, ckRHSNode, pivotKey);

                if (errCode != ErrorCode::Success)
                {
                    throw new std::exception("should not occur!");
                }                
            }

            ckLHSNode = prNodeDetails.first;

            vtNodes.pop_back();
        }

        return ErrorCode::Success;
    }

    template <typename IndexNodeType, typename DataNodeType>
    ErrorCode search(const KeyType& key, ValueType& value)
    {
        ErrorCode errCode = ErrorCode::Error;

#ifdef __CONCURRENT__
        std::vector<std::shared_lock<std::shared_mutex>> vtLocks;
        vtLocks.push_back(std::shared_lock<std::shared_mutex>(mutex));
#endif __CONCURRENT__

        ObjectUIDType ckCurrentNode = m_cktRootNodeKey.value();
        do
        {
            ObjectTypePtr prNodeDetails = m_ptrCache->getObject(ckCurrentNode);    //TODO: lock

#ifdef __CONCURRENT__
            vtLocks.push_back(std::shared_lock<std::shared_mutex>(prNodeDetails->mutex));
            vtLocks.erase(vtLocks.begin());
#endif __CONCURRENT__

            if (prNodeDetails == nullptr)
            {
                throw new std::exception("should not occur!");
            }

            if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*prNodeDetails->data))
            {
                std::shared_ptr<IndexNodeType> ptrIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*prNodeDetails->data);

                ckCurrentNode = ptrIndexNode->getChild(key);
            }
            else if (std::holds_alternative<std::shared_ptr<DataNodeType>>(*prNodeDetails->data))
            {
                std::shared_ptr<DataNodeType> ptrDataNode = std::get<std::shared_ptr<DataNodeType>>(*prNodeDetails->data);

                errCode = ptrDataNode->getValue(key, value);

                break;
            }
        } while (true);

        return errCode;
    }

    template <typename IndexNodeType, typename DataNodeType>
    ErrorCode remove(const KeyType& key)
    {
#ifdef __CONCURRENT__
        std::vector<std::unique_lock<std::shared_mutex>> vtLocks;
#endif __CONCURRENT__

        std::vector<std::pair<ObjectUIDType, ObjectTypePtr>> vtNodes;
        ObjectTypePtr ptrLastNode = nullptr, ptrCurrentNode = nullptr;
        ObjectUIDType ckLastNode, ckCurrentNode;

#ifdef __CONCURRENT__
        vtLocks.push_back(std::unique_lock<std::shared_mutex>(mutex));
#endif __CONCURRENT__

        ckCurrentNode = m_cktRootNodeKey.value();

        do
        {
            ptrCurrentNode = m_ptrCache->getObject(ckCurrentNode);    //TODO: lock
            
#ifdef __CONCURRENT__
            vtLocks.push_back(std::unique_lock<std::shared_mutex>(ptrCurrentNode->mutex));
#endif __CONCURRENT__

            if (ptrCurrentNode == nullptr)
            {
                throw new std::exception("should not occur!");
            }

            if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*ptrCurrentNode->data))
            {
                std::shared_ptr<IndexNodeType> ptrIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*ptrCurrentNode->data);

                if (ptrIndexNode->canTriggerMerge(m_nDegree))
                {
                    vtNodes.push_back(std::pair<ObjectUIDType, ObjectTypePtr>(ckLastNode, ptrLastNode));
                }
                else
                {
#ifdef __CONCURRENT__
                    if (vtLocks.size() > 3) //TODO: 3 seems to be working.. but how and why.. investiage....!
                    {
                        vtLocks.erase(vtLocks.begin());
                    }
#endif __CONCURRENT__
                    vtNodes.clear(); //TODO: release locks
                }

                ckLastNode = ckCurrentNode;
                ptrLastNode = ptrCurrentNode;

                ckCurrentNode = ptrIndexNode->getChild(key); // fid it.. there are two kinds of methods..
            }
            else if (std::holds_alternative<std::shared_ptr<DataNodeType>>(*ptrCurrentNode->data))
            {
                std::shared_ptr<DataNodeType> ptrDataNode = std::get<std::shared_ptr<DataNodeType>>(*ptrCurrentNode->data);

                ptrDataNode->remove(key);

                if (ptrDataNode->requireMerge(m_nDegree))
                {
                    vtNodes.push_back(std::pair<ObjectUIDType, ObjectTypePtr>(ckLastNode, ptrLastNode));
                    vtNodes.push_back(std::pair<ObjectUIDType, ObjectTypePtr>(ckCurrentNode, ptrCurrentNode));
                }
                else
                {
#ifdef __CONCURRENT__
                    vtLocks.clear();
#endif __CONCURRENT__
                    vtNodes.clear(); //TODO: release locks
                }

                break;
            }
        } while (true);

        ObjectUIDType ckChildNode;
        ObjectTypePtr ptrChildNode = nullptr;

        while (vtNodes.size() > 0)
        {
            std::pair<ObjectUIDType, ObjectTypePtr> prNodeDetails = vtNodes.back();

            if (prNodeDetails.second == nullptr)
            {
                if (vtNodes.size() != 1)
                {
                    throw new std::exception("should not occur!");
                }

                break;
            }

            if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*prNodeDetails.second->data))
            {
                std::shared_ptr<IndexNodeType> ptrParentIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*prNodeDetails.second->data);

                if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*ptrChildNode->data))
                {
                    std::optional<ObjectUIDType> dlt = std::nullopt;

                    std::shared_ptr<IndexNodeType> ptrChildIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*ptrChildNode->data);

                    if (ptrChildIndexNode->requireMerge(m_nDegree))
                    {
                        ptrParentIndexNode->template rebalanceIndexNode<std::shared_ptr<CacheType>, shared_ptr<IndexNodeType>>(m_ptrCache, ptrChildIndexNode, key, m_nDegree, ckChildNode, dlt);

                        if (dlt)
                        {
#ifdef __CONCURRENT__
                            if (*dlt == ckChildNode)
                            {
                                auto it = vtLocks.begin();
                                while (it != vtLocks.end()) {
                                    if ((*it).mutex() == &ptrChildNode->mutex)
                                    {
                                        break;
                                    }
                                    it++;
                                }

                                if (it != vtLocks.end())
                                    vtLocks.erase(it);
                            }
#endif __CONCURRENT__

                            m_ptrCache->remove(*dlt);
                        }

                        if (ptrParentIndexNode->getKeysCount() == 0)
                        {
                            m_cktRootNodeKey = ptrParentIndexNode->getChildAt(0);
                            //throw new exception("should not occur!");
                        }
                    }
                }
                else if (std::holds_alternative<std::shared_ptr<DataNodeType>>(*ptrChildNode->data))
                {
                    std::optional<ObjectUIDType> dlt = std::nullopt;

                    std::shared_ptr<DataNodeType> ptrChildDataNode = std::get<std::shared_ptr<DataNodeType>>(*ptrChildNode->data);
                    ptrParentIndexNode->template rebalanceDataNode<std::shared_ptr<CacheType>, shared_ptr<DataNodeType>>(m_ptrCache, ptrChildDataNode, key, m_nDegree, ckChildNode, dlt);

                    if (dlt)
                    {
#ifdef __CONCURRENT__
                        if (*dlt == ckChildNode)
                        {
                            auto it = vtLocks.begin();
                            while (it != vtLocks.end()) {
                                if ((*it).mutex() == &ptrChildNode->mutex)
                                {
                                    break;
                                }
                                it++;
                            }

                            if (it != vtLocks.end())
                                vtLocks.erase(it);
                        }
#endif __CONCURRENT__

                        m_ptrCache->remove(*dlt);
                    }

                    if (ptrParentIndexNode->getKeysCount() == 0)
                    {
                        m_cktRootNodeKey = ptrParentIndexNode->getChildAt(0);
                        //throw new exception("should not occur!");
                    }
                }
            }

            ckChildNode = prNodeDetails.first;
            ptrChildNode = prNodeDetails.second;

            vtNodes.pop_back();
        }

        return ErrorCode::Success;
    }

    template <typename IndexNodeType, typename DataNodeType>
    void print()
    {
        ObjectTypePtr ptrRootNode = m_ptrCache->getObjectOfType(m_cktRootNodeKey.value());
        if (std::holds_alternative<std::shared_ptr<IndexNodeType>>(*ptrRootNode->data))
        {
            std::shared_ptr<IndexNodeType> ptrIndexNode = std::get<std::shared_ptr<IndexNodeType>>(*ptrRootNode->data);

            ptrIndexNode->template print<std::shared_ptr<CacheType>, ObjectTypePtr, DataNodeType>(m_ptrCache, 0);
        }
        else if (std::holds_alternative<std::shared_ptr<DataNodeType>>(*ptrRootNode->data))
        {
            std::shared_ptr<DataNodeType> ptrDataNode = std::get<std::shared_ptr<DataNodeType>>(*ptrRootNode->data);

            ptrDataNode->print(0);
        }
    }
};