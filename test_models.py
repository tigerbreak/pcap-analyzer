from src.ai.deepseek_client import DeepSeekClient

def main():
    api_key = "sk-fizngoapnujlutpxoeugxlvitqwtupudnfeupudlvqjoqiyw"
    client = DeepSeekClient(api_key)
    
    print("正在获取可用的模型列表...")
    models = client.get_available_models()
    
    if models:
        print("\n可用的模型列表：")
        for model in models:
            print(f"- {model}")
    else:
        print("未能获取到模型列表")

if __name__ == "__main__":
    main() 