#pragma once
#include <iostream>
#include <mutex>
#include <shared_mutex>
#include <syncstream>
#include <thread>
#include <variant>
#include <typeinfo>

#include <iostream>
#include <fstream>

#include "ObjectFatUID.h"
#include "ErrorCodes.h"

template <typename T>
size_t doesCoreObjectContainIndex(const std::shared_ptr<T>& source) {
	return source->isIndexNode();
}

template <typename... Types>
size_t doesVariantContainIndex(std::variant<std::shared_ptr<Types>...>& source) {
	return std::visit([](const auto& ptr) -> size_t {
		return doesCoreObjectContainIndex(ptr);
		}, source);
}

template <typename T>
size_t getCoreObjectMemoryFootprint(const std::shared_ptr<T>& source) {
	return source->getMemoryFootprint();
}

template <typename... Types>
size_t getVariantMemoryFootprint(std::variant<std::shared_ptr<Types>...>& source) {
	return std::visit([](const auto& ptr) -> size_t {
		return getCoreObjectMemoryFootprint(ptr);
		}, source);
}

template <typename T>
std::shared_ptr<T> cloneSharedPtr(const std::shared_ptr<T>& source) {
	return source ? std::make_shared<T>(*source) : nullptr;
}

template <typename... Types>
std::variant<std::shared_ptr<Types>...> cloneVariant(const std::variant<std::shared_ptr<Types>...>& source) {
	using VariantType = std::variant<std::shared_ptr<Types>...>;

	return std::visit([](const auto& ptr) -> VariantType {
		return VariantType(cloneSharedPtr(ptr));
		}, source);
}

template <typename T>
void resetCoreValue(std::shared_ptr<T>& source) {
	source.reset();
}

template <typename... Types>
void resetVaraint(std::variant<std::shared_ptr<Types>...>& source) {
	return std::visit([](auto& ptr) {
		resetCoreValue(ptr);
		}, source);
}

template <typename CoreTypesMarshaller, typename... ValueCoreTypes>
class LRUCacheObject
{
private:
	typedef std::variant<std::shared_ptr<ValueCoreTypes>...> ValueCoreTypesWrapper;

public:
	typedef std::tuple<ValueCoreTypes...> ValueCoreTypesTuple;

private:
	bool m_bDirty;

	void* m_ptrCoreObject;
	uint8_t m_nCoreObjectType;

	//ValueCoreTypesWrapper m_objData;
	std::shared_mutex m_mtx;

	ObjectFatUID m_uid;
public:
	~LRUCacheObject()
	{
		if (m_ptrCoreObject != nullptr)
			delete m_ptrCoreObject;

		//resetVaraint(m_objData);
	}

	//template<class ValueCoreType>
	LRUCacheObject(void* ptrCoreObject, uint8_t nCoreObjectType)
		: m_bDirty(true)
	{
		m_ptrCoreObject = ptrCoreObject;
		m_nCoreObjectType = nCoreObjectType;
	}

	LRUCacheObject(std::fstream& fs)
		: m_bDirty(false)
	{
		CoreTypesMarshaller::template deserialize<ValueCoreTypesWrapper, ValueCoreTypes...>(fs, m_ptrCoreObject, m_nCoreObjectType);
	}

	LRUCacheObject(const char* szBuffer)
		: m_bDirty(false)
	{
		CoreTypesMarshaller::template deserialize<ValueCoreTypesWrapper, ValueCoreTypes...>(szBuffer, m_ptrCoreObject, m_nCoreObjectType);
	}

	inline void serialize(std::fstream& fs, uint8_t& uidObject, uint32_t& nBufferSize)
	{
		CoreTypesMarshaller::template serialize<ValueCoreTypes...>(fs, m_ptrCoreObject, m_nCoreObjectType, nBufferSize);
	}

	inline void serialize(char*& szBuffer, uint8_t& uidObject, uint32_t& nBufferSize)
	{
		CoreTypesMarshaller::template serialize<ValueCoreTypes...>(szBuffer, m_ptrCoreObject, m_nCoreObjectType, nBufferSize);
	}

	inline bool getDirtyFlag() const 
	{
		return m_bDirty;
	}

	inline void setDirtyFlag(bool bDirty)
	{
		m_bDirty = bDirty;
	}

	inline uint8_t getObjectType() const
	{
		return m_nCoreObjectType;
	}

	inline void* getInnerData()
	{
		return m_ptrCoreObject;
	}

	inline std::shared_mutex& getMutex()
	{
		return m_mtx;
	}

	inline bool tryLockObject()
	{
		return m_mtx.try_lock();
	}

	inline void unlockObject()
	{
		m_mtx.unlock();
	}

	inline size_t getMemoryFootprint()
	{
		return sizeof(*this);// fix this--> +getVariantMemoryFootprint(m_objData);
	}

	inline bool isIndexNode()
	{
		return sizeof(*this);// fix this--> +doesVariantContainIndex(m_objData);
	}
};