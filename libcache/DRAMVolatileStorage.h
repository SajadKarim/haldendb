#pragma once
#include <memory>
#include <unordered_map>

#include "ErrorCodes.h"

template <typename KeyType, typename ValueType>
class DRAMVolatileStorage
{
private:
	size_t m_nPoolSize;
	std::unordered_map<std::shared_ptr<KeyType>, std::shared_ptr<ValueType>, SharedPtrHash<KeyType>, SharedPtrEqual<KeyType>> m_mpObject;

public:
	DRAMVolatileStorage(size_t nPoolSize)
		: m_nPoolSize(nPoolSize)
	{
	}

	std::shared_ptr<ValueType> getObject(std::shared_ptr<KeyType> ptrKey)
	{
		if (m_mpObject.find(ptrKey) != m_mpObject.end())
		{
			return m_mpObject[ptrKey];
		}

		return nullptr;
	}

	CacheErrorCode addObject(std::shared_ptr<KeyType> ptrKey, std::shared_ptr<ValueType> ptrValue)
	{
		if (m_mpObject.size() >= m_nPoolSize)
		{
			return CacheErrorCode::Error;
		}

		m_mpObject[ptrKey] = ptrValue;

		return CacheErrorCode::Success;
	}
};

