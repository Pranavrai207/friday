import re

def test_math_logic(prompt):
    prompt_lower = prompt.lower().strip()
    math_keywords = ["plus", "minus", "into", "divide", "percent", "to", "over"]
    math_symbols = ["+", "-", "*", "/", "%"]
    
    has_math_op = any(re.search(rf'\b{op}\b', prompt_lower) for op in math_keywords) or any(op in prompt_lower for op in math_symbols)
    has_numbers = re.search(r'\d+', prompt_lower) or any(re.search(rf'\b{w}\b', prompt_lower) for w in ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"])
    
    print(f"Query: {prompt}")
    print(f"has_math_op: {has_math_op}, has_numbers: {has_numbers}")

    if has_math_op and has_numbers:
        try:
            w2n = {
                "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
                "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
            }
            calc_query = prompt_lower
            for word, num in w2n.items():
                calc_query = re.sub(rf'\b{word}\b', num, calc_query)
            
            calc_query = calc_query.replace("plus", "+").replace("minus", "-")
            calc_query = calc_query.replace("into", "*").replace("multiplied by", "*").replace("times", "*").replace("multiplied", "*")
            calc_query = calc_query.replace("divide by", "/").replace("divided by", "/").replace("divide", "/").replace("over", "/")
            
            calc_query = re.sub(r'(\d+)\s+to\s+(\d+)', r'\1/\2', calc_query)
            
            if "%" in calc_query or "percent" in calc_query:
                calc_query = re.sub(r'(\d+)\s*(%|percent)\s*of\s*(\d+)', r'\1/100*\3', calc_query)
                calc_query = calc_query.replace("%", "/100").replace("percent", "/100")
            
            calc_query = re.sub(r'[^0-9\+\-\*\/\.\(\) ]', ' ', calc_query)
            calc_query = re.sub(r'\s+', ' ', calc_query).strip()
            calc_query = re.sub(r'(\d+)\s+(\d+)', r'\1/\2', calc_query)
            
            print(f"Cleaned Query: {calc_query}")

            if any(op in calc_query for op in "+-*/") and re.search(r'\d', calc_query):
                final_expr = calc_query.replace(" ", "")
                print(f"Final Expr: {final_expr}")
                result = eval(final_expr)
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                elif isinstance(result, float):
                    result = round(result, 2)
                return f"That's {result}, boss."
            
        except Exception as e:
            print(f"Error: {e}")
    return "Fallback to LLM"

if __name__ == "__main__":
    queries = [
        "4 into 15 to 10 + 2",
        "five into ten into six",
        "20% of 500",
        "what is 2 plus 2",
        "who was Gandhi?"
    ]
    for q in queries:
        print(test_math_logic(q))
        print("-" * 20)
