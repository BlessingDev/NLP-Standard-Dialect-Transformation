#ifndef __TRAIN_UTIL_H__
#define __TRAIN_UTIL_H__
#include <tuple>
#include <boost/python/numpy.hpp>
#include <torch/torch.h>
#include <iostream>
#include <sstream>
#include <string>
#include <map>
#include "labeling_model.h"

namespace p = boost::python;
namespace np = boost::python::numpy;

p::dict ObjectToDict(PyObject*);

void InitBoostPython()
{
    //std::cout << "Init boost python" << std::endl;

    Py_Initialize();
    np::initialize();
}

void SetSeed(int s)
{
    torch::manual_seed(s);
}

bool IsCudaAvailable()
{
    return torch::cuda::is_available();
}

bool ExistFile(std::string& name)
{
    if (FILE *file = fopen(name.c_str(), "r")) {
        fclose(file);
        return true;
    } else {
        return false;
    }
}

void* InitModel(PyObject* args_pointer)
{
    //std::cout << "Init Model" << std::endl;

    p::dict args_dict = ObjectToDict(args_pointer);

    int num_embedding = p::extract<int>(args_dict["num_embedding"]);

    int embedding_size = 0;
    embedding_size = p::extract<int>(args_dict["embedding_size"]);

    int rnn_hidden_size = 0;
    rnn_hidden_size = p::extract<int>(args_dict["rnn_hidden_size"]);

    int class_num = 0;
    class_num = p::extract<int>(args_dict["class_num"]);

    TokenLabelingModel* model = new TokenLabelingModel(
        num_embedding, embedding_size, rnn_hidden_size, class_num
    );
    std::string device = p::extract<std::string>(p::str(args_dict["device"]));
    c10::DeviceType devType = c10::DeviceType::CPU;
    if(device.compare("cuda") == 0)
    {
        devType = c10::DeviceType::CUDA;
    }

    std::string temp_model_file = p::extract<std::string>(args_dict["temp_model_file"]);
    if(ExistFile(temp_model_file))
    {
        std::cout << "loaded from file" << std::endl;
        torch::load((*model), temp_model_file);
    }
    else
    {
        std::cout << "new model" << std::endl;
    }

    //std::cout << "model init with device " << device << std::endl;
    model->get()->to(devType);

    return (void*)model;
}

void FreeModel(void* model_void)
{
    //std::cout << "Free Model" << std::endl;
    TokenLabelingModel* model = (TokenLabelingModel*)model_void;

    delete model;
}

void SaveModel(void* model_pointer, std::string model_path)
{
    //std::cout << "Save Model" << std::endl;

    TokenLabelingModel* model = (TokenLabelingModel*)model_pointer;

    torch::save((*model), model_path);
}

std::vector<int> GetNparrSize(np::ndarray& np_arr)
{
    std::vector<int> size_vector;
    int nd = np_arr.get_nd();
    for (int i = 0; i < nd; i++)
    {
        size_vector.push_back(np_arr.shape(i));
    }

    return size_vector;
}

at::Tensor NdarrayToTensor(np::ndarray& array)
{
    //std::cout << "ndarr to tensor" << std::endl;
    std::vector<int> ori_shape = GetNparrSize(array);

    torch::Device device(torch::kCPU);
    if (torch::cuda::is_available())
        device = torch::Device(torch::kCUDA);
    auto opts = torch::TensorOptions().dtype(torch::kDouble);

    at::Tensor out_tensor;
    switch (ori_shape.size())
    {
    case 1:
        out_tensor = torch::from_blob(array.get_data(), {1, ori_shape[0]}, opts);
        break;
    case 2:
        out_tensor = torch::from_blob(array.get_data(), {ori_shape[0], ori_shape[1]}, opts);
        break;
    case 3:
        out_tensor = torch::from_blob(array.get_data(), {ori_shape[0], ori_shape[1], ori_shape[2]}, opts);
        break;
    default:
        std::cout << "3차원 이상 텐서입니다." << std::endl;
        break;
    }
    out_tensor = out_tensor.clone();
    out_tensor = out_tensor.to(device);

    //std::cout << "tensor from ndarray" << std::endl;
    //std::cout << out_tensor.sizes() << std::endl;
    //std::cout << out_tensor[0] << std::endl;
    return out_tensor;
}

np::ndarray ObjectToNdarray(PyObject* obj_pointer)
{
    //std::cout << "object to ndarray" << std::endl;
    p::handle<> handle(p::borrowed(obj_pointer));
    p::object arr_obj(handle);

    np::ndarray np_arr = np::from_object(arr_obj);

    //std::cout << "conversion complete" << std::endl;
    return np_arr;
}

p::list ObjectToList(PyObject* obj_pointer)
{
    //std::cout << "object to list" << std::endl;
    p::handle<> handle(p::borrowed(obj_pointer));
    p::object arr_obj(handle);

    p::list py_list = p::extract<p::list>(arr_obj);

    return py_list;
}

p::dict ObjectToDict(PyObject* obj_pointer)
{
    //std::cout << "object to dict" << std::endl;
    
    p::handle<> handle(p::borrowed(obj_pointer));
    p::object arr_obj(handle);

    p::dict py_dict = p::extract<p::dict>(arr_obj);

    return py_dict;
}

std::string ObjectToString(PyObject* obj_pointer)
{
    //std::cout << "object to dict" << std::endl;
    
    p::handle<> handle(p::borrowed(obj_pointer));
    p::object arr_obj(handle);

    std::string obj_str = p::extract<std::string>(arr_obj.attr("__str__"));

    return obj_str;
}


#endif