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

#include "ErrorCodes.h"

template <typename T>
std::shared_ptr<T> cloneSharedPtr(const std::shared_ptr<T>& source) {
	return source ? std::make_shared<T>(*source) : nullptr;
}

template <typename T>
void resetSharedPtr(std::shared_ptr<T>& source) {
	source.reset();
}

template <typename... Types>
std::variant<std::shared_ptr<Types>...> cloneVariant(const std::variant<std::shared_ptr<Types>...>& source) {
	using VariantType = std::variant<std::shared_ptr<Types>...>;

	return std::visit([](const auto& ptr) -> VariantType {
		return VariantType(cloneSharedPtr(ptr));
		}, source);
}

template <typename... Types>
void reset_(std::variant<std::shared_ptr<Types>...>& source) {
	using VariantType = std::variant<std::shared_ptr<Types>...>;

	return std::visit([](auto& ptr) {
		resetSharedPtr(ptr);
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
	ValueCoreTypesWrapper m_objData;
	std::shared_mutex m_mtx;

public:
	~LRUCacheObject()
	{
		reset_(m_objData);
		//std::visit({ ptr.reset(); }, m_objData);
	}

	template<class ValueCoreType>
	LRUCacheObject(std::shared_ptr<ValueCoreType> ptrCoreObject)
		: m_bDirty(true)	//TODO: should not it be false by default?
	{
		m_objData = ptrCoreObject;
	}

	LRUCacheObject(std::fstream& fs)
		: m_bDirty(false)
	{
		CoreTypesMarshaller::template deserialize<ValueCoreTypesWrapper, ValueCoreTypes...>(fs, m_objData);
	}

	LRUCacheObject(const char* szBuffer)
		: m_bDirty(false)
	{
		CoreTypesMarshaller::template deserialize<ValueCoreTypesWrapper, ValueCoreTypes...>(szBuffer, m_objData);
	}

	inline void serialize(std::fstream& fs, uint8_t& uidObjectType, uint32_t& nBufferSize)
	{
		CoreTypesMarshaller::template serialize<ValueCoreTypes...>(fs, m_objData, uidObjectType, nBufferSize);
	}

	inline void serialize(char*& szBuffer, uint8_t& uidObjectType, uint32_t& nBufferSize)
	{
		CoreTypesMarshaller::template serialize<ValueCoreTypes...>(szBuffer, m_objData, uidObjectType, nBufferSize);
	}

	inline const bool getDirtyFlag() const 
	{
		return m_bDirty;
	}

	inline void setDirtyFlag(bool bDirty)
	{
		m_bDirty = bDirty;
	}

	inline const ValueCoreTypesWrapper& getInnerData() const
	{
		return m_objData;
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
};