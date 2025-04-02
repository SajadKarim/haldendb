#pragma once
#include <variant>
#include <typeinfo>
#include <iostream>
#include <fstream>

class TypeMarshaller
{
public:
	template <typename... ValueCoreTypes>
	static void serialize(std::fstream& os, void* ptrObject, uint8_t& nObjectType, uint32_t& nBufferSize)
	{
		using TypeA = typename NthType<0, ValueCoreTypes...>::type;
		using TypeB = typename NthType<1, ValueCoreTypes...>::type;

		switch (nObjectType)
		{
			case TypeA::UID:
			{
				TypeA* _ptrObject = reinterpret_cast<TypeA*>(ptrObject);
				_ptrObject->writeToStream(os, nObjectType, nBufferSize);
				break;
			}
			case TypeB::UID:
			{
				TypeB* _ptrObject = reinterpret_cast<TypeB*>(ptrObject);
				_ptrObject->writeToStream(os, nObjectType, nBufferSize);
				break;
			}
		}
	}

	template <typename... ValueCoreTypes>
	static void serialize(char*& szBuffer, void* ptrObject, uint8_t& nObjectType, uint32_t& nBufferSize)
	{
		using TypeA = typename NthType<0, ValueCoreTypes...>::type;
		using TypeB = typename NthType<1, ValueCoreTypes...>::type;

		switch (nObjectType)
		{
			case TypeA::UID:
			{
				TypeA* _ptrObject = reinterpret_cast<TypeA*>(ptrObject);
				_ptrObject->serialize(szBuffer, nObjectType, nBufferSize);
				break;
			}
			case TypeB::UID:
			{	
				TypeB* _ptrObject = reinterpret_cast<TypeB*>(ptrObject);
				_ptrObject->serialize(szBuffer, nObjectType, nBufferSize);
				break;
			}
		}
	}

	template <typename ObjectType, typename... ValueCoreTypes>
	static void deserialize(std::fstream& fs, void*& ptrObject, uint8_t& nObjectType)
	{
		using TypeA = typename NthType<0, ValueCoreTypes...>::type;
		using TypeB = typename NthType<1, ValueCoreTypes...>::type;

		fs.read(reinterpret_cast<char*>(&nObjectType), sizeof(uint8_t));

		switch (nObjectType)
		{
		case TypeA::UID:
			ptrObject = new TypeA(fs);
			break;
		case TypeB::UID:
			ptrObject = new TypeB(fs);
			break;
		}
	}

	template <typename ObjectType, typename... ValueCoreTypes>
	static void deserialize(const char* szData, void*& ptrObject, uint8_t& nObjectType)
	{
		using TypeA = typename NthType<0, ValueCoreTypes...>::type;
		using TypeB = typename NthType<1, ValueCoreTypes...>::type;

		nObjectType = szData[0];

		switch (nObjectType)
		{
		case TypeA::UID:
			ptrObject = new TypeA(szData);
			break;
		case TypeB::UID:
			ptrObject = new TypeB(szData);
			break;
		default:
			std::cout << "Deserialization request for Uknown UID." << std::endl;
			throw new std::logic_error(".....");
		}
	}
};
