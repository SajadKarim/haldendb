#pragma once
#include <iostream>
#include <mutex>
#include <shared_mutex>
#include <syncstream>
#include <thread>
#include <variant>
#include <typeinfo>
#include <unordered_map>
#include <queue>
#include  <algorithm>
#include <tuple>
#include <condition_variable>
#include <assert.h>
#include "IFlushCallback.h"
#include "VariadicNthType.h"

#define FLUSH_COUNT 100
#define MIN_CACHE_FOOTPRINT 1024 * 1024	// Safe check!

using namespace std::chrono_literals;

template <typename ICallback, typename StorageType>
class CLOCKCache : public ICallback
{
	typedef CLOCKCache<ICallback, StorageType> SelfType;

public:
	typedef StorageType::ObjectUIDType ObjectUIDType;
	typedef StorageType::ObjectType ObjectType;
	typedef std::shared_ptr<ObjectType> ObjectTypePtr;

private:
	struct Item
	{
	public:
		ObjectUIDType m_uidSelf;
		ObjectTypePtr m_ptrObject;
		std::shared_ptr<Item> m_ptrPrev;
		std::shared_ptr<Item> m_ptrNext;
		bool m_bReferenceBit;  // CLOCK algorithm reference bit

		Item(const ObjectUIDType& uidObject, const ObjectTypePtr ptrObject)
			: m_ptrNext(nullptr)
			, m_ptrPrev(nullptr)
			, m_bReferenceBit(true)  // Set reference bit when accessed
		{
			m_uidSelf = uidObject;
			m_ptrObject = ptrObject;
		}

		~Item()
		{
			m_ptrPrev.reset();
			m_ptrNext.reset();
			m_ptrObject.reset();
		}
	};

	ICallback* m_ptrCallback;

	std::shared_ptr<Item> m_ptrHead;
	std::shared_ptr<Item> m_ptrTail;
	std::shared_ptr<Item> m_ptrClockHand;  // CLOCK algorithm hand pointer

	std::unique_ptr<StorageType> m_ptrStorage;

	int64_t m_nCacheFootprint;
	int64_t m_nCacheCapacity;
	std::unordered_map<ObjectUIDType, std::shared_ptr<Item>> m_mpObjects;
	std::unordered_map<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, ObjectTypePtr>> m_mpUIDUpdates;

#ifdef __CONCURRENT__
	bool m_bStop;

	std::thread m_threadCacheFlush;

	std::condition_variable_any m_cvUIDUpdates;

	mutable std::shared_mutex m_mtxCache;
	mutable std::shared_mutex m_mtxStorage;
#endif //__CONCURRENT__

public:
	~CLOCKCache()
	{
		// Debug output for CLOCK cache destruction
		std::cout << "[CLOCK DEBUG] CLOCKCache destructor called. Final cache size: " << m_mpObjects.size() 
		          << ", footprint: " << m_nCacheFootprint << std::endl;
		
#ifdef __CONCURRENT__
		m_bStop = true;
		m_threadCacheFlush.join();
#endif //__CONCURRENT__

		//presistCurrentCacheState();
		flushAllItemsToStorage();

		m_ptrHead.reset();
		m_ptrTail.reset();
		m_ptrClockHand.reset();
		m_ptrStorage.reset();

		m_mpObjects.clear();

		assert(m_nCacheFootprint == 0);
		
		std::cout << "[CLOCK DEBUG] CLOCKCache destructor completed." << std::endl;
	}

	template <typename... StorageArgs>
	CLOCKCache(size_t nCapacity, StorageArgs... args)
		: m_nCacheCapacity(nCapacity)
		, m_nCacheFootprint(0)
		, m_ptrHead(nullptr)
		, m_ptrTail(nullptr)
		, m_ptrClockHand(nullptr)
	{
#ifdef __TRACK_CACHE_FOOTPRINT__
		m_nCacheCapacity = m_nCacheCapacity < MIN_CACHE_FOOTPRINT ? MIN_CACHE_FOOTPRINT : m_nCacheCapacity;
#endif //__TRACK_CACHE_FOOTPRINT__

		m_ptrStorage = std::make_unique<StorageType>(args...);
		
		// Debug output for CLOCK cache initialization
		std::cout << "[CLOCK DEBUG] CLOCKCache initialized with capacity: " << m_nCacheCapacity << std::endl;
		
#ifdef __CONCURRENT__
		m_bStop = false;
		m_threadCacheFlush = std::thread(handlerCacheFlush, this);
#endif //__CONCURRENT__
	}

	void updateMemoryFootprint(int32_t nMemoryFootprint)
	{
#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		m_nCacheFootprint += nMemoryFootprint;
	}

	template <typename... InitArgs>
	CacheErrorCode init(ICallback* ptrCallback, InitArgs... args)
	{
//#ifdef __CONCURRENT__
//		m_ptrCallback = ptrCallback;
//		return m_ptrStorage->init(this/*getNthElement<0>(args...)*/);
//#else // ! __CONCURRENT__
//		return m_ptrStorage->init(ptrCallback/*getNthElement<0>(args...)*/);
//#endif //__CONCURRENT__

		m_ptrCallback = ptrCallback;

		return m_ptrStorage->init(this/*getNthElement<0>(args...)*/);
	}

	CacheErrorCode remove(const ObjectUIDType& uidObject)
	{
#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		auto it = m_mpObjects.find(uidObject);
		if (it != m_mpObjects.end()) 
		{

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint -= (*it).second->m_ptrObject->getMemoryFootprint();

			assert(m_nCacheFootprint >= 0);
#endif //__TRACK_CACHE_FOOTPRINT__

			removeFromClock((*it).second);
			m_mpObjects.erase(((*it).first));
			
			// TODO:
			// m_ptrStorage->remove(uidObject);
			return CacheErrorCode::Success;
		}

		// TODO:
		// m_ptrStorage->remove(uidObject);

		return CacheErrorCode::KeyDoesNotExist;
	}

	CacheErrorCode getObject(const ObjectUIDType& uidObject, ObjectTypePtr& ptrObject, std::optional<ObjectUIDType>& uidUpdated)
	{
#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache); // std::unique_lock due to LRU's linked-list update! is there any better way?
#endif //__CONCURRENT__

		if (m_mpObjects.find(uidObject) != m_mpObjects.end())
		{
			std::shared_ptr<Item> ptrItem = m_mpObjects[uidObject];
			ptrItem->m_bReferenceBit = true;  // Set reference bit for CLOCK algorithm
			ptrObject = ptrItem->m_ptrObject;

			return CacheErrorCode::Success;
		}

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_storage(m_mtxStorage); // TODO: requesting the same key?
		lock_cache.unlock();
#endif //__CONCURRENT__

		ObjectUIDType uidTemp = uidObject;

		if (m_mpUIDUpdates.find(uidObject) != m_mpUIDUpdates.end())
		{
#ifdef __CONCURRENT__
			std::optional< ObjectUIDType >& _condition = m_mpUIDUpdates[uidObject].first;
			m_cvUIDUpdates.wait(lock_storage, [&_condition] { return _condition != std::nullopt; });			
#endif //__CONCURRENT__

			uidUpdated = m_mpUIDUpdates[uidObject].first;

#ifdef __VALIDITY_CHECK__
			assert(uidUpdated != std::nullopt);
#endif //__VALIDITY_CHECK__

			m_mpUIDUpdates.erase(uidObject);
			uidTemp = *uidUpdated;
		}

#ifdef __CONCURRENT__
		lock_storage.unlock();
#endif //__CONCURRENT__

		ptrObject = m_ptrStorage->getObject(uidTemp);

		if (ptrObject != nullptr)
		{
			std::shared_ptr<Item> ptrItem = std::make_shared<Item>(uidTemp, ptrObject);

#ifdef __CONCURRENT__
			std::unique_lock<std::shared_mutex> re_lock_cache(m_mtxCache);

			if (m_mpObjects.find(uidTemp) != m_mpObjects.end())
			{
				std::cout << "Some other thread has also accessed the object." << std::endl;
				throw new std::logic_error("...");
/*
#ifdef __TRACK_CACHE_FOOTPRINT__
				m_nCacheFootprint -= m_mpObjects[uidTemp]->m_ptrObject->getMemoryFootprint();

				assert(m_nCacheFootprint >= 0);

				m_nCacheFootprint += ptrObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

				std::shared_ptr<Item> ptrItem = m_mpObjects[uidTemp];
				ptrItem->m_bReferenceBit = true;  // Set reference bit for CLOCK algorithm
				return CacheErrorCode::Success;
*/
			}
#endif //__CONCURRENT__

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint += ptrItem->m_ptrObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			m_mpObjects[ptrItem->m_uidSelf] = ptrItem;

			if (!m_ptrHead)
			{
				m_ptrHead = ptrItem;
				m_ptrTail = ptrItem;
				m_ptrClockHand = ptrItem;  // Initialize clock hand to first item
			}
			else
			{
				ptrItem->m_ptrNext = m_ptrHead;
				m_ptrHead->m_ptrPrev = ptrItem;
				m_ptrHead = ptrItem;
			}

#ifndef __CONCURRENT__
			flushItemsToStorage();
#endif //__CONCURRENT__

			return CacheErrorCode::Success;
		}

		return CacheErrorCode::Error;
	}

	// This method reorders the recently access objects. 
	// It is necessary to ensure that the objects are flushed in order otherwise a child object (data node) may preceed its parent (internal node).
	CacheErrorCode reorder(std::vector<std::pair<ObjectUIDType, ObjectTypePtr>>& vt, bool bEnsure = true)
	{
		// TODO: Need optimization.
#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		while (vt.size() > 0)
		{
			std::pair<ObjectUIDType, ObjectTypePtr> prNode = vt.back();

			if (m_mpObjects.find(prNode.first) != m_mpObjects.end())
			{
				std::shared_ptr<Item> ptrItem = m_mpObjects[prNode.first];
				ptrItem->m_bReferenceBit = true;  // Set reference bit for CLOCK algorithm
			}
			else
			{
				if (bEnsure)
				{
					std::cout << "Critical State: One or many entries in the reorder-list is missing in the cache." << std::endl;
					throw new std::logic_error(".....");   // TODO: critical log.
				}
			}

			vt.pop_back();
		}

		return CacheErrorCode::Success;
	}

	CacheErrorCode reorderOpt(std::vector<std::pair<ObjectUIDType, ObjectTypePtr>>& vtObjects, bool bEnsure = true)
	{
		size_t _test = vtObjects.size();
		std::vector<std::shared_ptr<Item>> vtItems;

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		while (vtObjects.size() > 0)
		{
			std::pair<ObjectUIDType, ObjectTypePtr> prObject = vtObjects.back();

			if (m_mpObjects.find(prObject.first) != m_mpObjects.end())
			{
				vtItems.emplace_back(m_mpObjects[prObject.first]);
			}

			vtObjects.pop_back();
		}

		if (bEnsure)
		{
			assert(_test == vtItems.size());
		}
		// Set reference bits for all items in CLOCK algorithm
		for (auto& ptrItem : vtItems)
		{
			ptrItem->m_bReferenceBit = true;
		}

		return CacheErrorCode::Success;
	}

//	template <typename Type>
//	CacheErrorCode getObjectOfType(const ObjectUIDType& uidObject, Type& ptrCoreObject, ObjectTypePtr& ptrStorageObject, std::optional<ObjectUIDType>& uidUpdated)
//	{
//#ifdef __CONCURRENT__
//		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
//#endif //__CONCURRENT__
//
//		if (m_mpObjects.find(uidObject) != m_mpObjects.end())
//		{
//			std::shared_ptr<Item> ptrItem = m_mpObjects[uidObject];
//			moveToFront(ptrItem);
//
//			if (std::holds_alternative<Type>(ptrItem->m_ptrObject->getInnerData()))
//			{
//				ptrStorageObject = ptrItem->m_ptrObject;
//				ptrCoreObject = std::get<Type>(ptrItem->m_ptrObject->getInnerData());
//				return CacheErrorCode::Success;
//			}
//
//			return CacheErrorCode::Error;
//		}
//
//#ifdef __CONCURRENT__
//		std::unique_lock<std::shared_mutex> lock_storage(m_mtxStorage);
//		lock_cache.unlock();
//#endif //__CONCURRENT__
//
//		const ObjectUIDType* uidTemp = &uidObject;
//		if (m_mpUIDUpdates.find(uidObject) != m_mpUIDUpdates.end())
//		{
//#ifdef __CONCURRENT__
//			std::optional< ObjectUIDType >& _condition = m_mpUIDUpdates[uidObject].first;
//			m_cvUIDUpdates.wait(lock_storage, [&_condition] { return _condition != std::nullopt; });
//#endif //__CONCURRENT__
//
//			uidUpdated = m_mpUIDUpdates[uidObject].first;
//
//#ifdef __VALIDITY_CHECK__
//			assert(uidUpdated != std::nullopt);
//#endif //__VALIDITY_CHECK__
//
//			m_mpUIDUpdates.erase(uidObject);
//			uidTemp = &(*uidUpdated);
//		}
//
//#ifdef __CONCURRENT__
//		lock_storage.unlock();
//#endif //__CONCURRENT__
//
//		ptrStorageObject = m_ptrStorage->getObject(*uidTemp);
//
//		if (ptrStorageObject != nullptr)
//		{
//#ifdef __CONCURRENT__
//			std::unique_lock<std::shared_mutex> re_lock_cache(m_mtxCache);
//
//			if (m_mpObjects.find(*uidTemp) != m_mpObjects.end())
//			{
//				// TODO: case where other threads might were accessing the same node and added it to the cache.
//				// but need to adjust memory_footprint.
//#ifdef __TRACK_CACHE_FOOTPRINT__
//				m_nCacheFootprint -= m_mpObjects[*uidTemp]->m_ptrObject->getMemoryFootprint();
//
//				assert(m_nCacheFootprint >= 0);
//					
//				m_nCacheFootprint += ptrStorageObject->getMemoryFootprint();
//#endif //__TRACK_CACHE_FOOTPRINT__
//
//				std::shared_ptr<Item> ptrItem = m_mpObjects[*uidTemp];
//				moveToFront(ptrItem);
//
//				if (std::holds_alternative<Type>(ptrItem->m_ptrObject->getInnerData()))
//				{
//					ptrCoreObject = std::get<Type>(ptrItem->m_ptrObject->getInnerData());
//					return CacheErrorCode::Success;
//				}
//
//				return CacheErrorCode::Error;
//			}
//#endif //__CONCURRENT__
//			std::shared_ptr<Item> ptrItem = std::make_shared<Item>(*uidTemp, ptrStorageObject);
//
//			m_mpObjects[ptrItem->m_uidSelf] = ptrItem;
//
//#ifdef __TRACK_CACHE_FOOTPRINT__
//			m_nCacheFootprint += ptrStorageObject->getMemoryFootprint();
//#endif //__TRACK_CACHE_FOOTPRINT__
//
//			if (!m_ptrHead)
//			{
//				m_ptrHead = ptrItem;
//				m_ptrTail = ptrItem;
//			}
//			else
//			{
//				ptrItem->m_ptrNext = m_ptrHead;
//				m_ptrHead->m_ptrPrev = ptrItem;
//				m_ptrHead = ptrItem;
//			}
//
//			if (std::holds_alternative<Type>(ptrItem->m_ptrObject->getInnerData()))
//			{
//				ptrCoreObject = std::get<Type>(ptrItem->m_ptrObject->getInnerData());
//			}
//
//#ifndef __CONCURRENT__
//			flushItemsToStorage();
//#endif //__CONCURRENT__
//
//			return CacheErrorCode::Error;
//		}
//
//		ptrCoreObject = nullptr;
//		ptrStorageObject = nullptr;
//		return CacheErrorCode::Error;
//	}

	template<class Type, typename... ArgsType>
	CacheErrorCode createObjectOfType(std::optional<ObjectUIDType>& uidObject, const ArgsType... args)
	{
		std::shared_ptr<Type> ptrCoreObject = std::make_shared<Type>(args...);

		std::shared_ptr<ObjectType> ptrStorageObject = std::make_shared<ObjectType>(ptrCoreObject);

		ObjectUIDType uidTemp;
		ObjectUIDType::createAddressFromVolatilePointer(uidTemp, Type::UID, reinterpret_cast<uintptr_t>(ptrStorageObject.get()));

		uidObject = uidTemp;

		std::shared_ptr<Item> ptrItem = std::make_shared<Item>(*uidObject, ptrStorageObject);

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		if (m_mpObjects.find(*uidObject) != m_mpObjects.end())
		{
			std::cout << "Critical State: UID for a newly created object already exist in the cache." << std::endl;
			throw new std::logic_error(".....");   // TODO: critical log.

			std::shared_ptr<Item> ptrItem = m_mpObjects[*uidObject];
			ptrItem->m_ptrObject = ptrStorageObject;
			ptrItem->m_bReferenceBit = true;  // Set reference bit for CLOCK algorithm
		}
		else
		{
			m_mpObjects[ptrItem->m_uidSelf] = ptrItem;

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint += ptrStorageObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			if (!m_ptrHead) 
			{
				m_ptrHead = ptrItem;
				m_ptrTail = ptrItem;
				m_ptrClockHand = ptrItem;  // Initialize clock hand to first item
			}
			else 
			{
				ptrItem->m_ptrNext = m_ptrHead;
				m_ptrHead->m_ptrPrev = ptrItem;
				m_ptrHead = ptrItem;
			}
		}

#ifndef __CONCURRENT__
		flushItemsToStorage();
#endif //__CONCURRENT__

		return CacheErrorCode::Success;
	}

	template<class Type, typename... ArgsType>
	CacheErrorCode createObjectOfType(std::optional<ObjectUIDType>& uidObject, ObjectTypePtr& ptrStorageObject, const ArgsType... args)
	{
		ptrStorageObject = std::make_shared<ObjectType>(std::make_shared<Type>(args...));

		ObjectUIDType uidTemp;
		ObjectUIDType::createAddressFromVolatilePointer(uidTemp, Type::UID, reinterpret_cast<uintptr_t>(ptrStorageObject.get()));
		
		uidObject = uidTemp;

		std::shared_ptr<Item> ptrItem = std::make_shared<Item>(*uidObject, ptrStorageObject);

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		if (m_mpObjects.find(*uidObject) != m_mpObjects.end())
		{
			std::cout << "Critical State: UID for a newly created object already exist in the cache." << std::endl;
			throw new std::logic_error(".....");   // TODO: critical log.
			std::shared_ptr<Item> ptrItem = m_mpObjects[*uidObject];
			ptrItem->m_ptrObject = ptrStorageObject;
			ptrItem->m_bReferenceBit = true;  // Set reference bit for CLOCK algorithm
		}
		else
		{
			m_mpObjects[ptrItem->m_uidSelf] = ptrItem;

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint += ptrStorageObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			if (!m_ptrHead)
			{
				m_ptrHead = ptrItem;
				m_ptrTail = ptrItem;
			}
			else
			{
				ptrItem->m_ptrNext = m_ptrHead;
				m_ptrHead->m_ptrPrev = ptrItem;
				m_ptrHead = ptrItem;
			}
		}

#ifndef __CONCURRENT__
		flushItemsToStorage();
#endif //__CONCURRENT__

		return CacheErrorCode::Success;
	}

	template<class Type, typename... ArgsType>
	CacheErrorCode createObjectOfType(std::optional<ObjectUIDType>& uidObject, std::shared_ptr<Type>& ptrCoreObject, const ArgsType... args)
	{
		ptrCoreObject = std::make_shared<Type>(args...);

		std::shared_ptr<ObjectType> ptrStorageObject = std::make_shared<ObjectType>(ptrCoreObject);

		uidObject = ObjectUIDType::createAddressFromVolatilePointer(Type::UID, reinterpret_cast<uintptr_t>(ptrStorageObject.get()));

		std::shared_ptr<Item> ptrItem = std::make_shared<Item>(*uidObject, ptrStorageObject);

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		if (m_mpObjects.find(*uidObject) != m_mpObjects.end())
		{
			std::cout << "Critical State: UID for a newly created object already exist in the cache." << std::endl;
			throw new std::logic_error(".....");   // TODO: critical log.
			std::shared_ptr<Item> ptrItem = m_mpObjects[*uidObject];
			ptrItem->m_ptrObject = ptrStorageObject;
			ptrItem->m_bReferenceBit = true;  // Set reference bit for CLOCK algorithm
		}
		else
		{
			m_mpObjects[&ptrItem->m_uidSelf] = ptrItem;

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint += ptrStorageObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			if (!m_ptrHead)
			{
				m_ptrHead = ptrItem;
				m_ptrTail = ptrItem;
			}
			else
			{
				ptrItem->m_ptrNext = m_ptrHead;
				m_ptrHead->m_ptrPrev = ptrItem;
				m_ptrHead = ptrItem;
			}
		}

#ifndef __CONCURRENT__
		flushItemsToStorage();
#endif //__CONCURRENT__

		return CacheErrorCode::Success;
	}

	void getCacheState(size_t& nObjectsLinkedList, size_t& nObjectsInMap)
	{
		nObjectsLinkedList = 0;
		std::shared_ptr<Item> ptrItem = m_ptrHead;

		while (ptrItem != nullptr)
		{
			nObjectsLinkedList++;
			ptrItem = ptrItem->m_ptrNext;
		} 

		nObjectsInMap = m_mpObjects.size();
	}

	CacheErrorCode flush()
	{
		flushDataItemsToStorage();
		//presistCurrentCacheState();

		return CacheErrorCode::Success;
	}

private:
	void moveToTail(std::shared_ptr<Item> tail, std::shared_ptr<Item> nodeToMove) 
	{
		if (tail == nullptr || nodeToMove == nullptr)
		{
			return;
		}

		if (nodeToMove->m_ptrPrev != nullptr)
		{
			nodeToMove->m_ptrPrev->m_ptrNext = nodeToMove->m_ptrNext;
		}
		else
		{
			tail = nodeToMove->m_ptrNext;
		}

		if (nodeToMove->m_ptrNext != nullptr)
		{
			nodeToMove->m_ptrNext->m_ptrPrev = nodeToMove->m_ptrPrev;
		}

		if (tail != nullptr) 
		{
			tail->m_ptrNext = nodeToMove;
			nodeToMove->m_ptrPrev = tail;
			nodeToMove->m_ptrNext = nullptr;
			tail = nodeToMove;
		}
		else 
		{
			tail = nodeToMove;
		}
	}

	void interchangeWithTail(std::shared_ptr<Item> currentNode) {
		if (currentNode == nullptr || currentNode == m_ptrTail) 
		{
			return;
		}

		if (currentNode->m_ptrPrev) 
		{
			currentNode->m_ptrPrev->m_ptrNext = currentNode->m_ptrNext;
		}
		else 
		{
			m_ptrHead = currentNode->m_ptrNext;
		}

		if (currentNode->m_ptrNext) 
		{
			currentNode->m_ptrNext->m_ptrPrev = currentNode->m_ptrPrev;
		}

		currentNode->m_ptrPrev = m_ptrTail;
		currentNode->m_ptrNext = nullptr;

		m_ptrTail->m_ptrNext = currentNode;

		m_ptrTail = currentNode;
	}

	// CLOCK algorithm: Find victim for replacement
	inline std::shared_ptr<Item> findClockVictim()
	{
		std::cout << "[CLOCK DEBUG] findClockVictim called, cache size: " << m_mpObjects.size() << std::endl;
		
		if (!m_ptrClockHand)
		{
			std::cout << "[CLOCK DEBUG] Clock hand is null, returning nullptr" << std::endl;
			return nullptr;
		}

		std::shared_ptr<Item> startHand = m_ptrClockHand;
		int sweepCount = 0;
		
		// Sweep through the circular list looking for a victim
		do
		{
			sweepCount++;
			if (!m_ptrClockHand->m_bReferenceBit)
			{
				// Found victim - item with reference bit = 0
				std::shared_ptr<Item> victim = m_ptrClockHand;
				// Move clock hand to next item
				m_ptrClockHand = m_ptrClockHand->m_ptrNext ? m_ptrClockHand->m_ptrNext : m_ptrHead;
				std::cout << "[CLOCK DEBUG] Found victim after " << sweepCount << " sweeps" << std::endl;
				return victim;
			}
			else
			{
				// Clear reference bit and move to next
				m_ptrClockHand->m_bReferenceBit = false;
				m_ptrClockHand = m_ptrClockHand->m_ptrNext ? m_ptrClockHand->m_ptrNext : m_ptrHead;
			}
		} while (m_ptrClockHand != startHand);

		// If all items have reference bit set, return the current hand position
		return m_ptrClockHand;
	}

	// For CLOCK algorithm, we don't need to move items to front
	// This method is kept for compatibility but just sets reference bits
	inline void setReferenceBits(const std::vector<std::shared_ptr<Item>>& itemList)
	{
		for (auto& ptrItem : itemList)
		{
			if (ptrItem)
			{
				ptrItem->m_bReferenceBit = true;
			}
		}
	}

	inline void removeFromClock(std::shared_ptr<Item> ptrItem)
	{
		// Update clock hand if it's pointing to the item being removed
		if (m_ptrClockHand == ptrItem)
		{
			m_ptrClockHand = ptrItem->m_ptrNext ? ptrItem->m_ptrNext : m_ptrHead;
		}

		if (ptrItem->m_ptrPrev != nullptr) 
		{
			ptrItem->m_ptrPrev->m_ptrNext = ptrItem->m_ptrNext;
		}
		else 
		{
			m_ptrHead = ptrItem->m_ptrNext;
			if (m_ptrHead != nullptr)
			{
				m_ptrHead->m_ptrPrev = nullptr;
			}
		}

		if (ptrItem->m_ptrNext != nullptr) 
		{
			ptrItem->m_ptrNext->m_ptrPrev = ptrItem->m_ptrPrev;
		}
		else 
		{
			m_ptrTail = ptrItem->m_ptrPrev;
			if (m_ptrTail != nullptr)
			{
				m_ptrTail->m_ptrNext = nullptr;
			}
		}

		// If this was the last item, reset clock hand
		if (m_ptrHead == nullptr)
		{
			m_ptrClockHand = nullptr;
		}
	}

	inline void flushItemsToStorage()
	{
#ifdef __CONCURRENT__
		std::vector<std::pair<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>> vtObjects;

		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);

#ifdef __TRACK_CACHE_FOOTPRINT__
		if (m_nCacheFootprint <= m_nCacheCapacity)
			return;

		while( m_nCacheFootprint >= m_nCacheCapacity)
#else //__TRACK_CACHE_FOOTPRINT__
		if (m_mpObjects.size() <= m_nCacheCapacity)
			return;

		size_t nFlushCount = m_mpObjects.size() - m_nCacheCapacity;
		for (size_t idx = 0; idx < nFlushCount; idx++)
#endif //__TRACK_CACHE_FOOTPRINT__
		{
			//std::cout << "..going to flush.." << std::endl;
			std::shared_ptr<Item> ptrItemToFlush = findClockVictim();
			
			if (!ptrItemToFlush)
			{
				break; // No victim found
			}
			
			if (ptrItemToFlush->m_ptrObject.use_count() > 1)
			{
				/* Info: 
				 * Should proceed with another victim?
				 * For now, we break to avoid infinite loops
				 */
				break; 
			}

			// Check if the object is in use
			if (!ptrItemToFlush->m_ptrObject->tryLockObject())
			{
				/* Info:
				 * Should proceed with another victim?
				 * For now, we break to avoid infinite loops
				 */
				break;
			}
			else
			{
				ptrItemToFlush->m_ptrObject->unlockObject();
			}

			vtObjects.push_back(std::make_pair(ptrItemToFlush->m_uidSelf, std::make_pair(std::nullopt, ptrItemToFlush->m_ptrObject)));

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint -= ptrItemToFlush->m_ptrObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			m_mpObjects.erase(ptrItemToFlush->m_uidSelf);
			removeFromClock(ptrItemToFlush);
			ptrItemToFlush.reset();
		}

		std::unique_lock<std::shared_mutex> lock_storage(m_mtxStorage);

		lock_cache.unlock();

		if (m_mpUIDUpdates.size() > 0)
		{
			m_ptrCallback->applyExistingUpdates(vtObjects, m_mpUIDUpdates);
		}

		// TODO: ensure that no other thread should touch the storage related params..
		size_t nNewOffset = 0;

		m_ptrCallback->prepareFlush(vtObjects, m_ptrStorage->getNextAvailableBlockOffset(), nNewOffset, m_ptrStorage->getBlockSize(), m_ptrStorage->getStorageType());

		//m_ptrCallback->prepareFlush(vtObjects, nPos, m_ptrStorage->getBlockSize(), m_ptrStorage->getMediaType());
		
		for(auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if ((*itObject).second.second.use_count() != 1)
			{
				std::cout << "Critical State: Can't proceed with the flushItemsToStorage operations as an object is in use." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			if (m_mpUIDUpdates.find((*itObject).first) != m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the flushItemsToStorage operations as object already exists in Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}
			m_mpUIDUpdates[(*itObject).first] = std::make_pair(std::nullopt, (*itObject).second.second);
		}

		lock_storage.unlock();
		
		//std::cout << m_ptrStorage->getNextAvailableBlockOffset() << ", " <<  nNewOffset << "=" << (nNewOffset - m_ptrStorage->getNextAvailableBlockOffset())*m_ptrStorage->getBlockSize() << std::endl;
		m_ptrStorage->addObjects(vtObjects, nNewOffset);

		std::unique_lock<std::shared_mutex> relock_storage(m_mtxStorage);

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if (m_mpUIDUpdates.find((*itObject).first) == m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: (flushItemsToStorage) Object with similar key does not exists in the Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			m_mpUIDUpdates[(*itObject).first].first = (*itObject).second.first;
		}
		relock_storage.unlock();

		m_cvUIDUpdates.notify_all();

		vtObjects.clear();
#else //__CONCURRENT__
		while (m_mpObjects.size() > m_nCacheCapacity)
		{
			if (m_ptrTail->m_ptrObject.use_count() > 1)
			{
				/* Info:
				 * Should proceed with the preceeding one?
				 * But since each operation reorders the items at the end, therefore, the prceeding items would be in use as well!
				 */
				break;
			}

			if (m_mpUIDUpdates.size() > 0)
			{
				m_ptrCallback->applyExistingUpdates(m_ptrTail->m_ptrObject, m_mpUIDUpdates);
			}

			if (m_ptrTail->m_ptrObject->getDirtyFlag())
			{

				ObjectUIDType uidUpdated;
				if (m_ptrStorage->addObject(m_ptrTail->m_uidSelf, m_ptrTail->m_ptrObject, uidUpdated) != CacheErrorCode::Success)
				{
					std::cout << "Critical State: Failed to add object to Storage." << std::endl;
					throw new std::logic_error(".....");   // TODO: critical log.
				}

				if (m_mpUIDUpdates.find(m_ptrTail->m_uidSelf) != m_mpUIDUpdates.end())
				{
					std::cout << "Critical State: Can't proceed with the flushItemsToStorage operations as object already exists in Updates' list." << std::endl;
					throw new std::logic_error(".....");   // TODO: critical log.
				}

				m_mpUIDUpdates[m_ptrTail->m_uidSelf] = std::make_pair(uidUpdated, m_ptrTail->m_ptrObject);
			}

			m_mpObjects.erase(m_ptrTail->m_uidSelf);

			std::shared_ptr<Item> ptrTemp = m_ptrTail;

			m_ptrTail = m_ptrTail->m_ptrPrev;

			if (m_ptrTail)
			{
				m_ptrTail->m_ptrNext = nullptr;
			}
			else
			{
				m_ptrHead = nullptr;
			}

			ptrTemp.reset();
		}
#endif //__CONCURRENT__
	}

	inline void flushAllItemsToStorage()
	{
		std::vector<std::pair<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>> vtObjects;

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		for (uint32_t idx = 0, idxend = m_mpObjects.size(); idx < idxend; idx++)
		{
			if (m_ptrTail->m_ptrObject.use_count() > 1)
			{
				std::cout << "Critical State: Can't proceed with the flushAllItemsToStorage operations as an object is in use." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			if (!m_ptrTail->m_ptrObject->tryLockObject())
			{
				std::cout << "Critical State: Can't proceed with the flushAllItemsToStorage operations as lock can't be acquired on object." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}
			else
			{
				m_ptrTail->m_ptrObject->unlockObject();
			}

			std::shared_ptr<Item> ptrItemToFlush = findClockVictim();

			vtObjects.push_back(std::make_pair(ptrItemToFlush->m_uidSelf, std::make_pair(std::nullopt, ptrItemToFlush->m_ptrObject)));

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint -= ptrItemToFlush->m_ptrObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			m_mpObjects.erase(ptrItemToFlush->m_uidSelf);
			removeFromClock(ptrItemToFlush);
			ptrItemToFlush.reset();
		}

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_storage(m_mtxStorage);

		lock_cache.unlock();
#endif //__CONCURRENT__

		if (m_mpUIDUpdates.size() > 0)
		{
			m_ptrCallback->applyExistingUpdates(vtObjects, m_mpUIDUpdates);
		}

		// TODO: ensure that no other thread should touch the storage related params..
		size_t nNewOffset = 0;

		m_ptrCallback->prepareFlush(vtObjects, m_ptrStorage->getNextAvailableBlockOffset(), nNewOffset, m_ptrStorage->getBlockSize(), m_ptrStorage->getStorageType());

		//m_ptrCallback->prepareFlush(vtObjects, nPos, m_ptrStorage->getBlockSize(), m_ptrStorage->getMediaType());

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if ((*itObject).second.second.use_count() != 1)
			{
				std::cout << "Critical State: Can't proceed with the flushAllItemsToStorage operations as an object is in use." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			if (m_mpUIDUpdates.find((*itObject).first) != m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the flushAllItemsToStorage operations as object already exists in Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			m_mpUIDUpdates[(*itObject).first] = std::make_pair(std::nullopt, (*itObject).second.second);
		}

#ifdef __CONCURRENT__
		lock_storage.unlock();
#endif //__CONCURRENT__

		m_ptrStorage->addObjects(vtObjects, nNewOffset);

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> relock_storage(m_mtxStorage);
#endif //__CONCURRENT__

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if (m_mpUIDUpdates.find((*itObject).first) == m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the flushAllItemsToStorage operations as object does not exists in Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			m_mpUIDUpdates[(*itObject).first].first = (*itObject).second.first;
		}

#ifdef __CONCURRENT__
		relock_storage.unlock();

		m_cvUIDUpdates.notify_all();
#endif //__CONCURRENT__

		vtObjects.clear();
	}

	inline void flushDataItemsToStorage()
	{
		std::vector<std::pair<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>> vtObjects;

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);
#endif //__CONCURRENT__

		std::shared_ptr<Item> ptrItemToFlush = m_ptrTail;

		for (uint32_t idx = 0, idxend = m_mpObjects.size(); idx < idxend; idx++)
		{
			if (ptrItemToFlush->m_ptrObject.use_count() > 1)
			{
				std::cout << "Critical State: Can't proceed with the flushDatatemsToStorage operations as an object is in use." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			if (!ptrItemToFlush->m_ptrObject->tryLockObject())
			{
				std::cout << "Critical State: Can't proceed with the flushDataItemsToStorage operations as lock can't be acquired on object." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}
			else
			{
				ptrItemToFlush->m_ptrObject->unlockObject();
			}

			vtObjects.push_back(std::make_pair(ptrItemToFlush->m_uidSelf, std::make_pair(std::nullopt, ptrItemToFlush->m_ptrObject)));

#ifdef __TRACK_CACHE_FOOTPRINT__
			m_nCacheFootprint -= ptrItemToFlush->m_ptrObject->getMemoryFootprint();
#endif //__TRACK_CACHE_FOOTPRINT__

			auto objectType = ptrItemToFlush->m_uidSelf.getObjectType();

			if (objectType == 101)
			{
				ptrItemToFlush = ptrItemToFlush->m_ptrPrev;
			}
			else
			{
				std::shared_ptr<Item> ptrTemp = ptrItemToFlush->m_ptrPrev;

				m_mpObjects.erase(ptrItemToFlush->m_uidSelf);

				if (m_ptrTail == ptrItemToFlush)
				{
					m_ptrTail = ptrItemToFlush->m_ptrPrev;

					ptrItemToFlush->m_ptrPrev = nullptr;
					ptrItemToFlush->m_ptrNext = nullptr;

					if (m_ptrTail)
					{
						m_ptrTail->m_ptrNext = nullptr;
					}
					else
					{
						m_ptrHead = nullptr;
					}

					ptrItemToFlush.reset();
				}
				else
				{

					ptrItemToFlush->m_ptrNext->m_ptrPrev = ptrItemToFlush->m_ptrPrev;
					ptrItemToFlush->m_ptrPrev->m_ptrNext = ptrItemToFlush->m_ptrPrev;

					ptrItemToFlush.reset();
				}

				ptrItemToFlush = ptrTemp;
			}
		}

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> lock_storage(m_mtxStorage);

		lock_cache.unlock();
#endif //__CONCURRENT__

		if (m_mpUIDUpdates.size() > 0)
		{
			m_ptrCallback->applyExistingUpdates(vtObjects, m_mpUIDUpdates);
		}

		// TODO: ensure that no other thread should touch the storage related params..
		size_t nNewOffset = 0;

		m_ptrCallback->prepareFlush(vtObjects, m_ptrStorage->getNextAvailableBlockOffset(), nNewOffset, m_ptrStorage->getBlockSize(), m_ptrStorage->getStorageType());

		//m_ptrCallback->prepareFlush(vtObjects, nPos, m_ptrStorage->getBlockSize(), m_ptrStorage->getMediaType());

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if ((*itObject).second.second.use_count() != 1)
			{
				std::cout << "Critical State: Can't proceed with the flushDatatemsToStorage operations as an object is in use." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			if (m_mpUIDUpdates.find((*itObject).first) != m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the flushDataItemsToStorage operations as object already exists in Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			m_mpUIDUpdates[(*itObject).first] = std::make_pair(std::nullopt, (*itObject).second.second);
		}

#ifdef __CONCURRENT__
		lock_storage.unlock();
#endif //__CONCURRENT__

		m_ptrStorage->addObjects(vtObjects, nNewOffset);

#ifdef __CONCURRENT__
		std::unique_lock<std::shared_mutex> relock_storage(m_mtxStorage);
#endif //__CONCURRENT__

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if (m_mpUIDUpdates.find((*itObject).first) == m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the flushDataItemsToStorage operations as object does not exists in Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			m_mpUIDUpdates[(*itObject).first].first = (*itObject).second.first;
		}

#ifdef __CONCURRENT__
		relock_storage.unlock();

		m_cvUIDUpdates.notify_all();
#endif //__CONCURRENT__

		vtObjects.clear();
	}

	inline void presistCurrentCacheState()
	{
#ifdef __CONCURRENT__
		std::vector<std::pair<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>> vtObjects;

		std::unique_lock<std::shared_mutex> lock_cache(m_mtxCache);

		std::shared_ptr<Item> ptrItemToFlush = m_ptrTail;

		for (uint32_t idx = 0, idxend = m_mpObjects.size(); idx < idxend; idx++)
		{
			if (ptrItemToFlush->m_ptrObject.use_count() > 1)
			{
				/* Info:
				 * Should proceed with the preceeding one?
				 * But since each operation reorders the items at the end, therefore, the prceeding items would be in use as well!
				 */
				break;
			}

			// Check if the object is in use
			if (!ptrItemToFlush->m_ptrObject->tryLockObject())
			{
				/* Info:
				 * Should proceed with the preceeding one?
				 * But since each operation reorders the items at the end, therefore, the prceeding items would be in use as well!
				 */
				break;
			}
			else
			{
				ptrItemToFlush->m_ptrObject->unlockObject();
			}

			vtObjects.push_back(std::make_pair(ptrItemToFlush->m_uidSelf, std::make_pair(std::nullopt, ptrItemToFlush->m_ptrObject)));

			ptrItemToFlush = ptrItemToFlush->m_ptrPrev;
		}

		std::unique_lock<std::shared_mutex> lock_storage(m_mtxStorage);

		lock_cache.unlock();

		if (m_mpUIDUpdates.size() > 0)
		{
			m_ptrCallback->applyExistingUpdates(vtObjects, m_mpUIDUpdates);
		}

		// TODO: ensure that no other thread should touch the storage related params..
		size_t nNewOffset = 0;
		m_ptrCallback->prepareFlush(vtObjects, m_ptrStorage->getNextAvailableBlockOffset(), nNewOffset, m_ptrStorage->getBlockSize(), m_ptrStorage->getStorageType());

		//m_ptrCallback->prepareFlush(vtObjects, nPos, m_ptrStorage->getBlockSize(), m_ptrStorage->getMediaType());

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if ((*itObject).second.second.use_count() != 2)
			{
				std::cout << "Critical State: Can't proceed with the presistCurrentCacheState operations as an object is in use." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			if (m_mpUIDUpdates.find((*itObject).first) != m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the presistCurrentCacheState operations as object already exists in Updates' list.." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}
			m_mpUIDUpdates[(*itObject).first] = std::make_pair(std::nullopt, (*itObject).second.second);
		}

		
		m_ptrStorage->addObjects(vtObjects, nNewOffset);

		for (auto itObject = vtObjects.begin(); itObject != vtObjects.end(); itObject++)
		{
			if (m_mpUIDUpdates.find((*itObject).first) == m_mpUIDUpdates.end())
			{
				std::cout << "Critical State: Can't proceed with the persistCurrentCacheStateoperations as object does not exist in Updates' list." << std::endl;
				throw new std::logic_error(".....");   // TODO: critical log.
			}

			m_mpUIDUpdates[(*itObject).first].first = (*itObject).second.first;
		}
		lock_storage.unlock();

		m_cvUIDUpdates.notify_all();

		vtObjects.clear();
#else //__CONCURRENT__
		while (m_mpObjects.size() > m_nCacheCapacity)
		{
			if (m_ptrTail->m_ptrObject.use_count() > 1)
			{
				/* Info:
				 * Should proceed with the preceeding one?
				 * But since each operation reorders the items at the end, therefore, the prceeding items would be in use as well!
				 */
				break;
			}

			if (m_mpUIDUpdates.size() > 0)
			{
				m_ptrCallback->applyExistingUpdates(m_ptrTail->m_ptrObject, m_mpUIDUpdates);
			}

			if (m_ptrTail->m_ptrObject->getDirtyFlag())
			{

				ObjectUIDType uidUpdated;
				if (m_ptrStorage->addObject(m_ptrTail->m_uidSelf, m_ptrTail->m_ptrObject, uidUpdated) != CacheErrorCode::Success)
				{
					std::cout << "Critical State: Failed to add object to Storage." << std::endl;
					throw new std::logic_error(".....");   // TODO: critical log.
				}

				if (m_mpUIDUpdates.find(m_ptrTail->m_uidSelf) != m_mpUIDUpdates.end())
				{
					std::cout << "Critical State: Recently add object to Storage doest not exist in Updates' list." << std::endl;
					throw new std::logic_error(".....");   // TODO: critical log.
				}

				m_mpUIDUpdates[m_ptrTail->m_uidSelf] = std::make_pair(uidUpdated, m_ptrTail->m_ptrObject);
			}

			m_mpObjects.erase(m_ptrTail->m_uidSelf);

			std::shared_ptr<Item> ptrTemp = m_ptrTail;

			m_ptrTail = m_ptrTail->m_ptrPrev;

			if (m_ptrTail)
			{
				m_ptrTail->m_ptrNext = nullptr;
			}
			else
			{
				m_ptrHead = nullptr;
			}

			ptrTemp.reset();
		}
#endif //__CONCURRENT__
	}

#ifdef __CONCURRENT__
	static void handlerCacheFlush(SelfType* ptrSelf)
	{
		do
		{
			//std::cout << "thread..." << std::endl;
			ptrSelf->flushItemsToStorage();

			std::this_thread::sleep_for(1ms);

		} while (!ptrSelf->m_bStop);
	}
#endif //__CONCURRENT__

#ifdef __TREE_WITH_CACHE__
public:
	void applyExistingUpdates(std::vector<std::pair<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>>& vtNodes
		, std::unordered_map<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>& mpUpdatedUIDs)
	{
	}

	void applyExistingUpdates(std::shared_ptr<ObjectType> ptrObject
		, std::unordered_map<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>& mpUpdatedUIDs)
	{
	}

	void prepareFlush(std::vector<std::pair<ObjectUIDType, std::pair<std::optional<ObjectUIDType>, std::shared_ptr<ObjectType>>>>& vtNodes
		, size_t nOffset, size_t& nNewOffset, size_t nBlockSize, ObjectUIDType::StorageMedia nMediaType)
	{
	}
#endif //__TREE_WITH_CACHE__
};
