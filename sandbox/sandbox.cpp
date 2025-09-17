#include <iostream>
#include "LRUCache.hpp"
#include "CLOCKCache.hpp"
#include "BPlusStore.hpp"
#include "NoCache.hpp"
#include "glog/logging.h"
#include <type_traits>
#include <variant>
#include <typeinfo>
#include "DataNode.hpp"
#include "IndexNode.hpp"
#include "DataNodeROpt.hpp"
#include "IndexNodeROpt.hpp"
#include <chrono>
#include <cassert>
#include "VolatileStorage.hpp"
#include "NoCacheObject.hpp"
#include "LRUCacheObject.hpp"
#include "CLOCKCacheObject.hpp"
#include "FileStorage.hpp"
#include "TypeMarshaller.hpp"
// #include "PMemStorage.hpp"  // Removed - using VolatileStorage only
#include "TypeUID.h"
#include <iostream>
#include "ObjectFatUID.h"
#include "ObjectUID.h"
#include <set>
#include <random>
#include <numeric>
#include "SSARCCache.hpp"
#include "SSARCCacheObject.hpp"
#include <string>
#include <fstream>
#include <iomanip>
#include <sstream>


#define __VALIDITY_CHECK__

// Forward declarations of helper functions
std::string getCurrentTimestamp();
void saveTestData(const std::vector<int>& data, const std::string& filename);
bool loadTestData(std::vector<int>& data, const std::string& filename);

#ifdef _MSC_VER
#define FILE_STORAGE_PATH "c:\\filestore.hdb"
#define PMEM_STORAGE_PATH "c:\\filestore.hdb"
#define PMEM_STORAGE_PATH_II "./datafile2"
#else
#define FILE_STORAGE_PATH "./filestore.hdb"
#define PMEM_STORAGE_PATH "./datafile1"
#define PMEM_STORAGE_PATH_II "./datafile2"
#endif

#ifdef __CONCURRENT__
template <typename BPlusStoreType>
void insert_concurent(BPlusStoreType* ptrTree, const std::vector<int>& random_numbers, int nRangeStart, int nRangeEnd)
{
    for (size_t nCntr = nRangeStart; nCntr < nRangeEnd; nCntr++)
    {
        ErrorCode ec = ptrTree->insert(random_numbers[nCntr], random_numbers[nCntr]);
        assert(ec == ErrorCode::Success);
    }
}

template <typename BPlusStoreType>
void reverse_insert_concurent(BPlusStoreType* ptrTree, int nRangeStart, int nRangeEnd)
{
    for (int nCntr = nRangeEnd - 1; nCntr >= nRangeStart; nCntr--)
    {
        ErrorCode ec = ptrTree->insert(nCntr, nCntr);
        assert(ec == ErrorCode::Success);
    }
}

template <typename BPlusStoreType>
void search_concurent(BPlusStoreType* ptrTree, const std::vector<int>& random_numbers, int nRangeStart, int nRangeEnd)
{
    for (size_t nCntr = nRangeStart; nCntr < nRangeEnd; nCntr++)
    {
        int nValue = 0;
        ErrorCode ec = ptrTree->search(random_numbers[nCntr], nValue);

        assert(random_numbers[nCntr] == nValue && ec == ErrorCode::Success);
    }
}

template <typename BPlusStoreType>
void search_not_found_concurent(BPlusStoreType* ptrTree, const std::vector<int>& random_numbers, int nRangeStart, int nRangeEnd) {
    for (size_t nCntr = nRangeStart; nCntr < nRangeEnd; nCntr++)
    {
        int nValue = 0;
        ErrorCode ec = ptrTree->search(random_numbers[nCntr], nValue);

        assert(ec == ErrorCode::KeyDoesNotExist);
    }
}

template <typename BPlusStoreType>
void delete_concurent(BPlusStoreType* ptrTree, const std::vector<int>& random_numbers, int nRangeStart, int nRangeEnd) {
    for (size_t nCntr = nRangeStart; nCntr < nRangeEnd; nCntr++)
    {
        ErrorCode ec = ptrTree->remove(random_numbers[nCntr]);

        assert(ec == ErrorCode::Success);
    }
}

template <typename BPlusStoreType>
void reverse_delete_concurent(BPlusStoreType* ptrTree, int nRangeStart, int nRangeEnd) {
    for (int nCntr = nRangeEnd - 1; nCntr >= nRangeStart; nCntr--)
    {
        ErrorCode ec = ptrTree->remove(nCntr);

        assert(ec == ErrorCode::KeyDoesNotExist);
    }
}

template <typename BPlusStoreType>
void threaded_test(BPlusStoreType* ptrTree, int degree, int total_entries, int thread_count)
{
    vector<std::thread> vtThreads;
    
    // Generate test data for threaded test
    std::vector<int> random_numbers(total_entries);
    std::iota(random_numbers.begin(), random_numbers.end(), 0); // Fill vector with 0 to total_entries-1
    
    std::random_device rd;
    std::mt19937 eng(rd());
    std::shuffle(random_numbers.begin(), random_numbers.end(), eng);
    
    // Save threaded test data
    std::string threadedDataFilename = "threaded_test_data_" + getCurrentTimestamp() + "_" + std::to_string(total_entries) + ".txt";
    saveTestData(random_numbers, threadedDataFilename);

    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (size_t nTestCntr = 0; nTestCntr < 1; nTestCntr++) {

        for (int nIdx = 0; nIdx < thread_count; nIdx++)
        {
            int nTotal = total_entries / thread_count;
            vtThreads.push_back(std::thread(insert_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
        }

        auto it = vtThreads.begin();
        while (it != vtThreads.end())
        {
            (*it).join();
            it++;
        }

        vtThreads.clear();

        for (int nIdx = 0; nIdx < thread_count; nIdx++)
        {
            int nTotal = total_entries / thread_count;
            vtThreads.push_back(std::thread(search_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
        }

        it = vtThreads.begin();
        while (it != vtThreads.end())
        {
            (*it).join();
            it++;
        }

        vtThreads.clear();

        for (int nIdx = 0; nIdx < thread_count; nIdx++)
        {
            int nTotal = total_entries / thread_count;
            vtThreads.push_back(std::thread(delete_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
        }   

        it = vtThreads.begin();
        while (it != vtThreads.end())
        {
            (*it).join();
            it++;
        }

        vtThreads.clear();

        for (int nIdx = 0; nIdx < thread_count; nIdx++)
        {
            int nTotal = total_entries / thread_count;
            vtThreads.push_back(std::thread(search_not_found_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
        }

        it = vtThreads.begin();
        while (it != vtThreads.end())
        {
            (*it).join();
            it++;
        }

        vtThreads.clear();

#ifdef __TREE_WITH_CACHE__
        size_t nLRU, nMap;
        ptrTree->getCacheState(nLRU, nMap);

        assert(nLRU == 1 && nMap == 1);
#endif //__TREE_WITH_CACHE__
    }
    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> int_test [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
}


template <typename BPlusStoreType>
void fptree_threaded_test(BPlusStoreType* ptrTree, int total_entries, int thread_count)
{
    vector<std::thread> vtThreads;
    
    // Generate test data for fptree threaded test
    std::vector<int> random_numbers(total_entries);
    std::iota(random_numbers.begin(), random_numbers.end(), 0);
    
    std::random_device rd;
    std::mt19937 eng(rd());
    std::shuffle(random_numbers.begin(), random_numbers.end(), eng);
    
    // Save fptree test data
    std::string fptreeDataFilename = "fptree_test_data_" + getCurrentTimestamp() + "_" + std::to_string(total_entries) + ".txt";
    saveTestData(random_numbers, fptreeDataFilename);

    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (int nIdx = 0; nIdx < thread_count; nIdx++)
    {
        int nTotal = total_entries / thread_count;
        vtThreads.push_back(std::thread(insert_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
    }

    auto it = vtThreads.begin();
    while (it != vtThreads.end())
    {
        (*it).join();
        it++;
    }

    vtThreads.clear();

    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> insert (threaded) [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    std::this_thread::sleep_for(std::chrono::seconds(10));

    ptrTree->flush();

    begin = std::chrono::steady_clock::now();

    for (int nIdx = 0; nIdx < thread_count; nIdx++)
    {
        int nTotal = total_entries / thread_count;
        vtThreads.push_back(std::thread(search_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
    }

    it = vtThreads.begin();
    while (it != vtThreads.end())
    {
        (*it).join();
        it++;
    }

    vtThreads.clear();

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> search (threaded) [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    std::this_thread::sleep_for(std::chrono::seconds(10));

    begin = std::chrono::steady_clock::now();

    for (int nIdx = 0; nIdx < thread_count; nIdx++)
    {
        int nTotal = total_entries / thread_count;
        vtThreads.push_back(std::thread(delete_concurent<BPlusStoreType>, ptrTree, std::cref(random_numbers), nIdx * nTotal, nIdx * nTotal + nTotal));
    }

    it = vtThreads.begin();
    while (it != vtThreads.end())
    {
        (*it).join();
        it++;
    }

    vtThreads.clear();

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> delete (threaded) [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

#ifdef __TREE_WITH_CACHE__
        size_t nLRU, nMap;
        ptrTree->getCacheState(nLRU, nMap);

        assert(nLRU == 1 && nMap == 1);
#endif //__TREE_WITH_CACHE__
}
#endif //__CONCURRENT__

// Helper function to generate timestamp for filename
std::string getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S");
    ss << "_" << std::setfill('0') << std::setw(3) << ms.count();
    return ss.str();
}

// Helper function to save test data to file
void saveTestData(const std::vector<int>& data, const std::string& filename) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << " for writing" << std::endl;
        return;
    }
    
    file << data.size() << std::endl;
    for (const auto& value : data) {
        file << value << std::endl;
    }
    file.close();
    std::cout << "Test data saved to: " << filename << std::endl;
}

// Helper function to load test data from file
bool loadTestData(std::vector<int>& data, const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << " for reading" << std::endl;
        return false;
    }
    
    size_t size;
    file >> size;
    data.resize(size);
    
    for (size_t i = 0; i < size; ++i) {
        file >> data[i];
    }
    file.close();
    std::cout << "Test data loaded from: " << filename << " (size: " << size << ")" << std::endl;
    return true;
}

template <typename BPlusStoreType>
void int_test(BPlusStoreType* ptrTree, size_t nMaxNumber)
{
    std::vector<int> random_numbers(nMaxNumber);
    
    // Generate filename with timestamp
    std::string dataFilename = "test_data_" + getCurrentTimestamp() + "_" + std::to_string(nMaxNumber) + ".txt";
    
    // Option to hardcode a specific filename for debugging (uncomment and modify as needed)
    // To use a specific test data file, uncomment the next 4 lines and comment out the generation section
    // std::string hardcodedFilename = "test_data_20250917_194215_819_100000.txt";
    // if (loadTestData(random_numbers, hardcodedFilename)) {
    //     std::cout << "Using hardcoded test data from: " << hardcodedFilename << std::endl;
    // } else {
    
    // Always generate new random data (comment this section if using hardcoded file above)
    std::iota(random_numbers.begin(), random_numbers.end(), 1); // Fill vector with 1 to nMaxNumber
    
    std::random_device rd; // Obtain a random number from hardware
    std::mt19937 eng(rd()); // Seed the generator
    std::shuffle(random_numbers.begin(), random_numbers.end(), eng);
    
    // Save the generated data
    saveTestData(random_numbers, dataFilename);
    std::cout << "Generated new test data and saved to: " << dataFilename << std::endl;
    // } // Uncomment this if using hardcoded file above

    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (size_t nTestCntr = 0; nTestCntr < 2; nTestCntr++)
    {
        for (size_t nCntr = 0; nCntr < nMaxNumber; nCntr = nCntr + 1)
        {
            ErrorCode code = ptrTree->insert(random_numbers[nCntr], random_numbers[nCntr]);
            assert(code == ErrorCode::Success);
        }

        //std::ofstream out_1("d:\\tree_post_insert_0.txt");
        //ptrTree->print(out_1);
        //out_1.flush();
        //out_1.close();

        for (size_t nCntr = 0; nCntr < nMaxNumber; nCntr++)
        {
            int nValue = 0;
            ErrorCode code = ptrTree->search(random_numbers[nCntr], nValue);

            assert(nValue == random_numbers[nCntr]);
        }

        for (size_t nCntr = 0; nCntr < nMaxNumber; nCntr = nCntr + 2)
        {
            ErrorCode code = ptrTree->remove(random_numbers[nCntr]);

            assert(code == ErrorCode::Success);
        }
        for (size_t nCntr = 1; nCntr < nMaxNumber; nCntr = nCntr + 2)
        {
            ErrorCode code = ptrTree->remove(random_numbers[nCntr]);

            assert(code == ErrorCode::Success);
        }

        for (int nCntr = 0; nCntr < nMaxNumber; nCntr++)
        {
            int nValue = 0;
            ErrorCode code = ptrTree->search(random_numbers[nCntr], nValue);

            assert(code == ErrorCode::KeyDoesNotExist);
        }

#ifdef __TREE_WITH_CACHE__
        size_t nLRU, nMap;
        ptrTree->getCacheState(nLRU, nMap);

        assert(nLRU == 1 && nMap == 1);
#endif //__TREE_WITH_CACHE__
}

    for (size_t nTestCntr = 0; nTestCntr < 2; nTestCntr++)
    {
        for (int nCntr = nMaxNumber; nCntr >= 0; nCntr = nCntr - 2)
        {
            ErrorCode ec = ptrTree->insert(nCntr, nCntr);
            assert(ec == ErrorCode::Success);

        }
        for (int nCntr = nMaxNumber - 1; nCntr >= 0; nCntr = nCntr - 2)
        {
            ErrorCode ec = ptrTree->insert(nCntr, nCntr);
            assert(ec == ErrorCode::Success);
        }

        for (int nCntr = 0; nCntr < nMaxNumber; nCntr++)
        {
            int nValue = 0;
            ErrorCode ec = ptrTree->search(nCntr, nValue);

            assert(nValue == nCntr && ec == ErrorCode::Success);
        }

        for (int nCntr = nMaxNumber; nCntr >= 0; nCntr = nCntr - 2)
        {
            ErrorCode ec = ptrTree->remove(nCntr);
            assert(ec == ErrorCode::Success);
        }

        for (int nCntr = nMaxNumber - 1; nCntr >= 0; nCntr = nCntr - 2)
        {
            ErrorCode ec = ptrTree->remove(nCntr);
            assert(ec == ErrorCode::Success);
        }

        for (int nCntr = 0; nCntr < nMaxNumber; nCntr++)
        {
            int nValue = 0;
            ErrorCode ec = ptrTree->search(nCntr, nValue);

            assert(ec == ErrorCode::KeyDoesNotExist);
    }

#ifdef __TREE_WITH_CACHE__
        size_t nLRU, nMap;
        ptrTree->getCacheState(nLRU, nMap);

        assert(nLRU == 1 && nMap == 1);
#endif //__TREE_WITH_CACHE__
    }

    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> int_test [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
}
template <typename BPlusStoreType>
void string_test(BPlusStoreType* ptrTree, int degree, int total_entries)
{
    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (size_t nTestCntr = 0; nTestCntr < 10; nTestCntr++)
    {
        for (size_t nCntr = 0; nCntr < total_entries; nCntr = nCntr + 2)
        {
            ptrTree->insert(to_string(nCntr), to_string(nCntr));
        }
        for (size_t nCntr = 1; nCntr < total_entries; nCntr = nCntr + 2)
        {
            ptrTree->insert(to_string(nCntr), to_string(nCntr));
        }

        for (size_t nCntr = 0; nCntr < total_entries; nCntr++)
        {
            string nValue = "";
            ErrorCode code = ptrTree->search(to_string(nCntr), nValue);

            assert(nValue == to_string(nCntr));
        }

        for (size_t nCntr = 0; nCntr < total_entries; nCntr = nCntr + 2)
        {
            ErrorCode code = ptrTree->remove(to_string(nCntr));
        }
        for (size_t nCntr = 1; nCntr < total_entries; nCntr = nCntr + 2)
        {
            ErrorCode code = ptrTree->remove(to_string(nCntr));
        }

        for (size_t nCntr = 0; nCntr < total_entries; nCntr++)
        {
            string nValue = "";
            ErrorCode code = ptrTree->search(to_string(nCntr), nValue);

            assert(code == ErrorCode::KeyDoesNotExist);
        }

#ifdef __TREE_WITH_CACHE__
        size_t nLRU, nMap;
        ptrTree->getCacheState(nLRU, nMap);

        assert(nLRU == 1 && nMap == 1);
#endif //__TREE_WITH_CACHE__
    }

    for (size_t nTestCntr = 0; nTestCntr < 10; nTestCntr++)
    {
        for (int nCntr = total_entries - 1; nCntr >= 0; nCntr = nCntr - 2)
        {
            ptrTree->insert(to_string(nCntr), to_string(nCntr));
        }
        for (int nCntr = total_entries; nCntr >= 0; nCntr = nCntr - 2)
        {
            ptrTree->insert(to_string(nCntr), to_string(nCntr));
        }

        for (int nCntr = 0; nCntr < total_entries; nCntr++)
        {
            string nValue = "";
            ErrorCode code = ptrTree->search(to_string(nCntr), nValue);

            assert(nValue == to_string(nCntr));
        }

        for (int nCntr = total_entries; nCntr >= 0; nCntr = nCntr - 2)
        {
            ErrorCode code = ptrTree->remove(to_string(nCntr));
        }
        for (int nCntr = total_entries - 1; nCntr >= 0; nCntr = nCntr - 2)
        {
            ErrorCode code = ptrTree->remove(to_string(nCntr));
        }

        for (int nCntr = 0; nCntr < total_entries; nCntr++)
        {
            string nValue = "";
            ErrorCode code = ptrTree->search(to_string(nCntr), nValue);

            assert(code == ErrorCode::KeyDoesNotExist);
        }

#ifdef __TREE_WITH_CACHE__
        size_t nLRU, nMap;
        ptrTree->getCacheState(nLRU, nMap);

        assert(nLRU == 1 && nMap == 1);
#endif //__TREE_WITH_CACHE__
    }

    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> int_test [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
}

void test_for_ints()
{
    for( size_t nDegree = 32; nDegree < 256; nDegree = nDegree + 32)
    {
        std::cout << "||||||| Running 'test_for_ints' for nDegree:" << nDegree << std::endl;
        
#ifndef __TREE_WITH_CACHE__
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef uintptr_t ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef BPlusStore<KeyType, ValueType, NoCache<ObjectUIDType, NoCacheObject, DataNodeType, IndexNodeType>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree);
            ptrTree.template init<DataNodeType>();

            int_test<BPlusStoreType>(&ptrTree, 5000000);
        }
#else //__TREE_WITH_CACHE__
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef CLOCKCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, CLOCKCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, CLOCKCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024);
            ptrTree.template init<DataNodeType>();

            int_test<BPlusStoreType>(&ptrTree, 100000);
        }
        /*{
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef SSARCCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, SSARCCache<ICallback, FileStorage<ICallback, ObjectUIDType, SSARCCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024* 1024 * 1024, FILE_STORAGE_PATH);
            ptrTree.init<DataNodeType>();

            int_test<BPlusStoreType>(&ptrTree, 100000);
        }*/
        // PMemStorage test commented out - using VolatileStorage only
        /*
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef SSARCCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, SSARCCache<ICallback, PMemStorage<ICallback, ObjectUIDType, SSARCCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
#ifndef _MSC_VER
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, PMEM_STORAGE_PATH);
            ptrTree.init<DataNodeType>();
            int_test<BPlusStoreType>(&ptrTree, 1000000);
#endif //_MSC_VER
        }
        */
        /*{
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef SSARCCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, SSARCCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, SSARCCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024);
            ptrTree.template init<DataNodeType>();

            int_test<BPlusStoreType>(&ptrTree, 100000);
        }
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef SSARCCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, SSARCCache<ICallback, FileStorage<ICallback, ObjectUIDType, SSARCCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);
            ptrTree.init<DataNodeType>();

            int_test<BPlusStoreType>(&ptrTree, 100000);
        }*/
        // PMemStorage test commented out - using VolatileStorage only
        /*
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef SSARCCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, SSARCCache<ICallback, PMemStorage<ICallback, ObjectUIDType, SSARCCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
#ifndef _MSC_VER
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, PMEM_STORAGE_PATH);
            ptrTree.init<DataNodeType>();
            int_test<BPlusStoreType>(&ptrTree, 1000000);
#endif //_MSC_VER
        }
        */
#endif //__TREE_WITH_CACHE__

        std::cout << std::endl;
    }
}

void test_for_string()
{
    for (size_t nDegree = 3; nDegree < 40; nDegree++) 
    {
        std::cout << "||||||| Running 'test_for_string' for nDegree:" << nDegree << std::endl;

#ifndef __TREE_WITH_CACHE__
        {
            typedef string KeyType;
            typedef string ValueType;
            typedef uintptr_t ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_STRING_STRING> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_STRING_STRING> IndexNodeType;

            typedef BPlusStore<KeyType, ValueType, NoCache<ObjectUIDType, NoCacheObject, DataNodeType, IndexNodeType>> BPlusStoreType;
            BPlusStoreType* ptrTree1 = new BPlusStoreType(nDegree);
            ptrTree1->init<DataNodeType>();

            string_test<BPlusStoreType>(ptrTree1, nDegree, 100000);
        }
#else //__TREE_WITH_CACHE__
        {
        }
#endif //__TREE_WITH_CACHE__
        std::cout << std::endl;
    }
}

void test_for_threaded()
{
#ifdef __CONCURRENT__
    for (size_t nDegree = 200; nDegree < 1200; nDegree = nDegree + 200)
    {
        std::cout << "||||||| Running 'test_for_threaded' for nDegree:" << nDegree << std::endl;
//continue;
#ifndef __TREE_WITH_CACHE__
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef uintptr_t ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef BPlusStore<KeyType, ValueType, NoCache<ObjectUIDType, NoCacheObject, DataNodeType, IndexNodeType>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree);
            ptrTree.template init<DataNodeType>();

            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 10000000, 20);
        }
#else //__TREE_WITH_CACHE__
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef CLOCKCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;


            typedef BPlusStore<ICallback, KeyType, ValueType, CLOCKCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, CLOCKCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024);
            ptrTree.template init<DataNodeType>();

            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 1000000, 12);
        }
        /*{
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef LRUCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, FileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);
            ptrTree.template init<DataNodeType>();

            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 1000000, 12);
        }*/
        // PMemStorage test commented out - using VolatileStorage only
        /*
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef LRUCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, PMemStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
#ifndef _MSC_VER
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, PMEM_STORAGE_PATH);
            ptrTree.template init<DataNodeType>();
            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 1000000, 12);
#endif //_MSC_VER
        }
        */
        /*{
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef LRUCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;


            typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024);
            ptrTree.template init<DataNodeType>();

            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 1000000, 12);
        }
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef LRUCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, FileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);
            ptrTree.template init<DataNodeType>();

            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 1000000, 12);
        }*/
        // PMemStorage test commented out - using VolatileStorage only
        /*
        {
            typedef int KeyType;
            typedef int ValueType;
            typedef ObjectFatUID ObjectUIDType;

            typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
            typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

            typedef LRUCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
            typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

            typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, PMemStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
#ifndef _MSC_VER
            BPlusStoreType ptrTree(nDegree, 100, 1024, 10ULL * 1024 * 1024 * 1024, PMEM_STORAGE_PATH);
            ptrTree.template init<DataNodeType>();
            threaded_test<BPlusStoreType>(&ptrTree, nDegree, 1000000, 6);
#endif //_MSC_VER
        }
        */
#endif //__TREE_WITH_CACHE__

        std::cout << std::endl;
    }
#endif //__CONCURRENT__
}

void quick_test()
{
    for (size_t idx = 0; idx < 5; idx++) {
        test_for_ints();
        //test_for_string();
        test_for_threaded();
    }
}

struct CHAR16 {
    char data[16];

    // Default constructor (trivial)
    CHAR16() = default;

    // Parameterized constructor
    CHAR16(const char* str) {
        std::memset(data, 0, sizeof(data));
#ifndef _MSC_VER
        strncpy(data, str, sizeof(data) - 1);
#else _MSC_VER
        strncpy_s(data, sizeof(data), str, sizeof(data) - 1); 
#endif _MSC_VER
    }

    // Define the < operator for comparison
    bool operator<(const CHAR16& other) const {
        return std::strncmp(data, other.data, sizeof(data)) < 0;
    }

    // Define the == operator for comparison
    bool operator==(const CHAR16& other) const {
        return std::strncmp(data, other.data, sizeof(data)) == 0;
    }
};



template <typename BPlusStoreType>
void fptree_test(BPlusStoreType* ptrTree, size_t nMaxNumber)
{
    //std::ifstream file("/home/skarim/Reproducibility/benchmarks/microbenchmarks/values_int.dat"); 
    std::ifstream file("/home/skarim/Reproducibility/benchmarks/microbenchmarks/values_string.dat"); 

    std::vector<CHAR16> random_numbers;
    //int64_t number; 
    std::string line;
    
    while (std::getline(file, line)) 
    { 
        CHAR16 itm;
        std::memcpy(&itm.data, line.c_str(), 15);
        itm.data[15] = '\0';
//	    number = std::stoull(line);
        random_numbers.push_back(itm);
    } 
    
    //r (const auto &num : random_numbers)
    //
    //  std::cout << num << std::endl; 
   //
	std::cout << "---" <<  random_numbers.size() << std::endl;

    //std::vector<int> random_numbers(nMaxNumber);//50000000);
    //std::iota(random_numbers.begin(), random_numbers.end(), 1); // Fill vector with 1 to 5,000,000    
    //std::random_device rd; // Obtain a random number from hardware
    //std::mt19937 eng(rd()); // Seed the generator
    //std::shuffle(random_numbers.begin(), random_numbers.end(), eng);

    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nMaxNumber; nCntr++)
    {
        ptrTree->insert(random_numbers[nCntr], 0);
    }

    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> insert [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
 //return;
    std::this_thread::sleep_for(std::chrono::seconds(10));

    begin = std::chrono::steady_clock::now();

    ptrTree->flush();

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> flush [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    std::this_thread::sleep_for(std::chrono::seconds(10));

    begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nMaxNumber; nCntr++)
    {
        int64_t nValue = 0;
        ErrorCode ec = ptrTree->search(random_numbers[nCntr], nValue);

        //assert(nValue == random_numbers[nCntr]);
    }

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> search [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    std::this_thread::sleep_for(std::chrono::seconds(10));
return;
//ptrTree->flush();

    begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nMaxNumber; nCntr++)
    {
        int64_t nValue = 0;
        ErrorCode ec = ptrTree->remove(random_numbers[nCntr]);

        //assert(nValue == random_numbers[nCntr]);
    }

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> delete [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
}

void fptree_bm()
{
#ifdef __TREE_WITH_CACHE__
    typedef CHAR16 KeyType;
    typedef int64_t ValueType;

    typedef ObjectFatUID ObjectUIDType;

    typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    //typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

    //typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

    typedef LRUCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
    typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

    //typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, FileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(24, 1024, 512, 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);

    typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(24, 1024, 4096, 10ULL * 1024 * 1024 * 1024);

    // PMemStorage commented out - using VolatileStorage only
    // typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, PMemStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
	
    //typedef BPlusStore<KeyType, ValueType, NoCache<ObjectUIDType, NoCacheObject, DataNodeType, IndexNodeType>> BPlusStoreType;
    
    // Single-threaded test
    {
        size_t nMaxNumber = 5000000;
	
        for (size_t nDegree = 32; nDegree < 4000; nDegree = nDegree + 10)
        {
		//break;
            size_t nInternalNodeSize = (nDegree - 1) * sizeof(ValueType) + nDegree * sizeof(ObjectUIDType) + sizeof(int*);
            size_t nTotalInternalNodes = nMaxNumber / nDegree;
            //size_t nMemoryOfNodes = nTotalNodes * nNodeSize;
            //size_t nMemoryOfData = nMaxNumber * sizeof(KeyType);
            size_t nTotalMemory = nTotalInternalNodes * nInternalNodeSize;
            size_t nTotalMemoryInMB = nTotalMemory / (1024 * 1024);

            size_t nBlockSize = nInternalNodeSize > 256 ? 256 : 128;

            std::cout
                << "Order = " << nDegree
                << ", Total IN (n) = " << nTotalInternalNodes
                << ", Total Memory (MB) = " << nTotalMemoryInMB
                << ", Block Size = " << nBlockSize
                << std::endl;

            for (size_t nCntr = 0; nCntr < 1; nCntr++)
            {
                //BPlusStoreType ptrTree(nDegree, nTotalMemoryInMB, nBlockSize, 25ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);
                BPlusStoreType ptrTree(nDegree, nTotalInternalNodes, nBlockSize, 120ULL * 1024 * 1024 * 1024); // VolatileStorage doesn't need file path
                ptrTree.init<DataNodeType>();

                std::cout << "Iteration = " << nCntr + 1 << std::endl;
                fptree_test<BPlusStoreType>(&ptrTree, nMaxNumber);
                std::this_thread::sleep_for(std::chrono::seconds(10));
                //break;
            }
	    std::cout << std::endl;
            //std::this_thread::sleep_for(std::chrono::seconds(10));
            //break;
        }
    }
return;
//#ifdef __CONCURRENT__
//    // Multi-threaded test
//    {
//        size_t nMaxNumber = 50000000;
//        //size_t nMaxNumber = 100000;
//        for (size_t nDegree = 1000; nDegree < 2001; nDegree = nDegree + 100)
//        {
//            size_t nInternalNodeSize = (nDegree - 1) * sizeof(ValueType) + nDegree * sizeof(ObjectUIDType) + sizeof(int*);
//            size_t nTotalInternalNodes = nMaxNumber / nDegree;
//            //size_t nMemoryOfNodes = nTotalNodes * nNodeSize;
//            //size_t nMemoryOfData = nMaxNumber * sizeof(KeyType);
//            size_t nTotalMemory = nTotalInternalNodes * nInternalNodeSize;
//            size_t nTotalMemoryInMB = nTotalMemory / (1024 * 1024);
//
//            size_t nBlockSize = nInternalNodeSize > 256 ? 256 : 128;
//
//            std::cout
//                << "Order = " << nDegree
//                << ", Total Memory (B) = " << nTotalMemory
//                << ", Total Memory (MB) = " << nTotalMemoryInMB
//                << ", Block Size = " << nBlockSize
//                << std::endl;
//
//            for (size_t nCntr = 0; nCntr < 1; nCntr++)
//            {
//                //BPlusStoreType ptrTree(nDegree, nTotalMemoryInMB, nBlockSize, 25ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);
//                BPlusStoreType ptrTree(nDegree, nTotalMemoryInMB, nBlockSize, 120ULL * 1024 * 1024 * 1024, PMEM_STORAGE_PATH_II);
//                ptrTree.init<DataNodeType>();
//
//                std::cout << "Iteration = " << nCntr + 1 << std::endl;
//                fptree_threaded_test<BPlusStoreType>(&ptrTree, nMaxNumber, 12);
//                std::this_thread::sleep_for(std::chrono::seconds(10));
//            }
//	    std::cout << std::endl;
//            std::this_thread::sleep_for(std::chrono::seconds(10));
//        }
//    }
//#endif //__CONCURRENT__
#endif //__TREE_WITH_CACHE__

}

//struct KeyTypeEx {
//    uint64_t value1;
//    uint64_t value2;
//
//
//    // Default constructor
//    KeyTypeEx() = default;
//
//    // Parameterized constructor
//    KeyTypeEx(uint64_t v1, uint64_t v2) : value1(v1), value2(v2) {}
//
//    // Define the < operator for comparison
//    bool operator<(const KeyTypeEx& other) const {
//        if (value1 != other.value1) {
//            return value1 < other.value1;
//        }
//        return value2 < other.value2;
//    }
//    
//    bool operator==(const KeyTypeEx& other) const {
//        return value1 == other.value1 && value2 == other.value2;
//    }
//};

struct KeyTypeEx {
    char data[16];

    // Default constructor (trivial)
    KeyTypeEx() = default;

    // Parameterized constructor
    KeyTypeEx(const char* str) {
        std::memset(data, 0, sizeof(data));
#ifndef _MSC_VER
        strncpy(data, str, sizeof(data) - 1);
#else _MSC_VER
        strncpy_s(data, sizeof(data), str, sizeof(data) - 1);
#endif _MSC_VER
    }

    // Define the < operator for comparison
    bool operator<(const KeyTypeEx& other) const {
        return std::strncmp(data, other.data, sizeof(data)) < 0;
    }

    // Define the == operator for comparison
    bool operator==(const KeyTypeEx& other) const {
        return std::strncmp(data, other.data, sizeof(data)) == 0;
    }
};



std::string intToFixedLengthString(int value, size_t length = 16) {
    char buffer[16]; // Create a buffer of 9 chars to include the null terminator 
    snprintf(buffer, sizeof(buffer), "%08d", value); // Convert the integer to a string return 
    return std::string(buffer); // Return the string 
}

void cache_team_test()
{
#ifdef __TREE_WITH_CACHE__

    typedef KeyTypeEx KeyType;
    typedef KeyTypeEx ValueType;
    typedef ObjectFatUID ObjectUIDType;
    
    //typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    //typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

    typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

    typedef SSARCCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
    typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

    //typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, FileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(24, 1024, 512, 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);

    //typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(3, 10, 32, 1ULL * 1024 * 1024 * 1024);
     
    typedef BPlusStore<ICallback, KeyType, ValueType, SSARCCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, SSARCCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    BPlusStoreType ptrTree(3, 10, 32, 1ULL * 1024 * 1024 * 1024);

    //typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, PMemStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(48, 4096 ,512 , 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);

    ptrTree.init<DataNodeType>();

    size_t nTotalEntries = 50000;
    std::vector<int> random_numbers(nTotalEntries);//50000000);
    std::iota(random_numbers.begin(), random_numbers.end(), 1); // Fill vector with 1 to 5,000,000
    std::random_device rd; // Obtain a random number from hardware
    std::mt19937 eng(rd()); // Seed the generator
    std::shuffle(random_numbers.begin(), random_numbers.end(), eng);

    KeyTypeEx ch_numbers[50000];

    std::vector<KeyTypeEx> random_numbersexs;// (nTotalEntries);
    for (size_t i = 0; i < nTotalEntries; ++i) {
        std::string str = intToFixedLengthString(random_numbers[i]); 
        std::memcpy(&ch_numbers[i], str.c_str(), 16); // Copy the string to KeyType array 
        /*KeyTypeEx a(random_numbers[i], random_numbers[i]);
        a.value1 = a.value2 = random_numbers[i];
        random_numbersexs.push_back(a);*/
    }


    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nTotalEntries; nCntr++)
    {
        ptrTree.insert(ch_numbers[nCntr], ch_numbers[nCntr]);
    }

    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> insert [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nTotalEntries; nCntr++)
    {
        ValueType nValue;
        ErrorCode ec = ptrTree.search(ch_numbers[nCntr], nValue);

        assert(nValue == ch_numbers[nCntr]);
    }

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> search [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nTotalEntries; nCntr++)
    {
        //ErrorCode ec = ptrTree.remove(random_numbers[nCntr]);

        //assert(ec == ErrorCode::Success);
    }

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> delete [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    begin = std::chrono::steady_clock::now();

    //ptrTree.flush();

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> flush [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
#endif //__TREE_WITH_CACHE__


}


int main(int argc, char* argv[])
{
    //cache_team_test();
    //return 0;

    //fptree_bm();
    quick_test();
    //return 0;

    typedef int KeyType;
    typedef int ValueType;

#ifdef __TREE_WITH_CACHE__
    typedef ObjectFatUID ObjectUIDType;

    typedef DataNodeROpt<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    typedef IndexNodeROpt<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;
    
    //typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    //typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

    typedef CLOCKCacheObject<TypeMarshaller, DataNodeType, IndexNodeType> ObjectType;
    typedef IFlushCallback<ObjectUIDType, ObjectType> ICallback;

    //typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, FileStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(24, 1024, 512, 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);
    
    typedef BPlusStore<ICallback, KeyType, ValueType, CLOCKCache<ICallback, VolatileStorage<ICallback, ObjectUIDType, CLOCKCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    BPlusStoreType ptrTree(24, 1024, 1024, 10ULL * 1024 * 1024 * 1024);
    
    //typedef BPlusStore<ICallback, KeyType, ValueType, LRUCache<ICallback, PMemStorage<ICallback, ObjectUIDType, LRUCacheObject, TypeMarshaller, DataNodeType, IndexNodeType>>> BPlusStoreType;
    //BPlusStoreType ptrTree(48, 4096 ,512 , 10ULL * 1024 * 1024 * 1024, FILE_STORAGE_PATH);

    ptrTree.init<DataNodeType>();
#else //__TREE_WITH_CACHE__
    typedef int KeyType;
    typedef int ValueType;
    typedef uintptr_t ObjectUIDType;

    typedef DataNode<KeyType, ValueType, ObjectUIDType, TYPE_UID::DATA_NODE_INT_INT> DataNodeType;
    typedef IndexNode<KeyType, ValueType, ObjectUIDType, DataNodeType, TYPE_UID::INDEX_NODE_INT_INT> IndexNodeType;

    typedef BPlusStore<KeyType, ValueType, NoCache<ObjectUIDType, NoCacheObject, DataNodeType, IndexNodeType>> BPlusStoreType;
    BPlusStoreType ptrTree(24);
    ptrTree.init<DataNodeType>();
#endif //__TREE_WITH_CACHE__

    size_t nTotalEntries = 100000;
    std::vector<int> random_numbers(nTotalEntries);//50000000);
    std::iota(random_numbers.begin(), random_numbers.end(), 1); // Fill vector with 1 to 5,000,000
    std::random_device rd; // Obtain a random number from hardware
    std::mt19937 eng(rd()); // Seed the generator
    std::shuffle(random_numbers.begin(), random_numbers.end(), eng);

    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr < nTotalEntries; nCntr = nCntr++)
    {
        ptrTree.insert(random_numbers[nCntr], random_numbers[nCntr]);
    }

    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    std::cout
        << ">> insert [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

#ifdef __TREE_WITH_CACHE__
    begin = std::chrono::steady_clock::now();

    ptrTree.flush();

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> flush [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;
#endif //__TREE_WITH_CACHE__

    begin = std::chrono::steady_clock::now();

    for (size_t nCntr = 0; nCntr <= nTotalEntries; nCntr = nCntr + 2)
    {
        ValueType nValue = 0;
        ErrorCode ec = ptrTree.search(random_numbers[nCntr], nValue);

        assert(nValue == random_numbers[nCntr]);
    }

    end = std::chrono::steady_clock::now();
    std::cout
        << ">> search [Time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "us"
        << ", " << std::chrono::duration_cast<std::chrono::nanoseconds> (end - begin).count() << "ns]"
        << std::endl;

    for (size_t nCntr = 0; nCntr < nTotalEntries; nCntr++)
    {
        ErrorCode ec = ptrTree.remove(nCntr);
    }

    for (size_t nCntr = 0; nCntr < nTotalEntries; nCntr++)
    {
        ValueType nValue = 0;
        ErrorCode ec = ptrTree.search(nCntr, nValue);

        assert(ec == ErrorCode::KeyDoesNotExist);
    }

    std::cout << "End.";
    return 0;
}
