from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import transformers

print("=== SYSTEM CHECK ===")
print(f"PyTorch version: {torch.__version__}")
print(f"Transformers version: {transformers.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
print(f"CUDA version: {torch.version.cuda}")

print("\n=== MODEL COMPATIBILITY CHECK ===")
try:
    # Test tokenizer loading
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-270m-it")
    print("✓ Tokenizer loaded successfully")
    
    # Test model loading
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        "google/gemma-3-270m-it",
        device_map="auto",
        torch_dtype="auto"
    )
    print("✓ Model loaded successfully")
    
    # Test basic inference
    print("Testing inference...")
    inputs = tokenizer("Hello, how are you?", return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=20)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"✓ Inference test passed: {response}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("Please check:")
    print("1. Internet connection for model download")
    print("2. PyTorch CUDA installation")
    print("3. Enough disk space (~1.5GB for this model)")

print("\n=== QUANTIZATION SUPPORT CHECK ===")
try:
    from transformers import BitsAndBytesConfig
    from peft import prepare_model_for_kbit_training
    print("✓ bitsandbytes and peft available for QLoRA")
except ImportError as e:
    print(f"✗ Missing packages: {e}")
    print("Run: pip install bitsandbytes peft")

print("\n=== RECOMMENDATION ===")
if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= 8 * 1024**3:
    print("✓ Your system is ready for QLoRA training!")
else:
    print("⚠️  You might need to use CPU or reduced settings")