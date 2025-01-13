from easynmt import EasyNMT

from dataset import NMTPredictionDataset, generate_raw_nmt_batches
from utils import set_seed_everywhere

import os
import argparse
import json
import torch
import tqdm.cli as tqdm
import numpy as np
import re

import cython_module.cvocabulary as cvocabulary
import cython_module.cjamo as cjamo
import cython_module.sentence as sentence

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

def init_dataset(args) -> tuple:
    data_set = None

    # 데이터셋를 만듭니다.
    data_set = NMTPredictionDataset.load_dataset(args.prediction_json)
    
    return data_set

def idx_to_tokens(indices, vocab):
    token_list = []

    for idx in indices:
        if idx == vocab.end_seq_index:
            break
        token_list.append(vocab.lookup_index(idx))
    
    return token_list

def decode_with_bpe(indices, vocab, tokenizer):
    token_list = idx_to_tokens(indices, vocab)

    token_ids = [tokenizer.token_to_id(token) for token in token_list]
    token_ids = [token for token in token_ids if token is not None]

    deocded_sentence = tokenizer.decode(token_ids)

    return deocded_sentence

def decode_with_sp(indices, vocab, tokenizer):
    token_list = idx_to_tokens(indices, vocab)

    decoded_sentence = tokenizer.decode(token_list)
    decoded_sentence = decoded_sentence.replace("<UNK>", " <UNK>")

    return decoded_sentence
    
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--prediction_json",
        type=str,
        required=True
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="opus-mt"
    )
    parser.add_argument(
        "--gpus",
        type=str,
        default="0,1"
    )
    parser.add_argument(
        "--target_lang",
        type=str,
        default="en"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32
    )

    args = parser.parse_args()
    
    '''args = parser.parse_args([
        "--prediction_json", "/workspace/model_storage/dia_to_sta/gangwon/jamo/prediction.json", 
        "--output_path", "/workspace/translation_output/chungcheong/test.json",
        "--batch_size", "4"
    ])'''

    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus
    
    if not torch.cuda.is_available():
        args.device = "cpu"
    else:
        args.device = "cuda"

    args.device = torch.device(args.device)
        
    print("{} device 사용".format(args.device))

    data_set = init_dataset(args)

    max_gen_length = 60
    model = EasyNMT(args.model_name)
    

    test_bar = tqdm.tqdm(desc='split=test',
                        total=data_set.get_num_batches(args.batch_size), 
                        position=1, 
                        leave=True)

    running_acc = 0.0
    #vectorizer.max_source_length = 60
    #vectorizer.max_target_length = max_gen_length - 1
    batch_generator = generate_raw_nmt_batches(data_set, 
                                        batch_size=args.batch_size, 
                                        shuffle=False,
                                        drop_last=False,
                                        device="cpu")
    results = []
    try:
        for batch_index, batch_dict in enumerate(batch_generator):
            batch_size = len(batch_dict["prediction"])
            
            pred_sentences = batch_dict["prediction"]
            
            pred_target_sentences = model.translate(pred_sentences, source_lang="ko", target_lang=args.target_lang)
            
            m = sentence.batch_sentence_to_result_dict(
                [pred_sentences, pred_target_sentences],
                ["prediction_source", "prediction_target"],
                batch_size
            )
            
            results.extend(m)
            
            # 진행 상태 막대 업데이트
            #test_bar.set_postfix(acc=running_acc)
            test_bar.update()
        
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
        with open(args.output_path, mode="xt", encoding="utf-8") as fp:
            fp.write(json.dumps(results, ensure_ascii=False))
    
    except KeyboardInterrupt:
        
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
        with open(args.output_path, mode="xt", encoding="utf-8") as fp:
            fp.write(json.dumps(results, ensure_ascii=False))
        print("반복 중지")


if __name__ == "__main__":
    main()