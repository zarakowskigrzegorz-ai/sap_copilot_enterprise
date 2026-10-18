import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer

# Konfiguracja ścieżek i modelu bazowego
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_ID = "meta-llama/Meta-Llama-3-8B"  # Możesz też użyć "unsloth/llama-3-8b-Instruct-bnb-4bit" dla szybszego treningu
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "dataset.jsonl")  # Wygenerowany plik w ml_pipeline/data/
OUTPUT_DIR = os.path.join(BASE_DIR, "sap_copilot_adapter")

def train_sap_model():
    # Konfiguracja kwantyzacji 4-bitowej (QLoRA)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Model bazowy z kwantyzacją
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    model = prepare_model_for_kbit_training(model)

    # Konfiguracja adaptera PEFT (LoRA)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # Wczytanie przygotowanego datasetu JSONL
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    # Parametry treningu
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=10,
        num_train_epochs=1,  # Na początek 1 epoka w zupełności wystarczy do testu
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        save_strategy="epoch"
    )

    # Inicjalizacja SFTTrainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    print("Uruchamianie treningu QLoRA dla asystenta SAP...")
    trainer.train()

    # Zapis gotowego adaptera
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Zakończono. Adapter zapisanany w katalogu: {OUTPUT_DIR}")

if __name__ == "__main__":
    train_sap_model()