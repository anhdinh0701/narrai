import asyncio
import time
import httpx
import json

API_URL = "http://localhost:8000/api"

async def test_case(name, prompt, length="medium"):
    print(f"\n{'='*50}\nBắt đầu test case: {name}\n{'='*50}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Trending Topics
        print("1. Kiểm tra Trending Topics...")
        t0 = time.time()
        res = await client.get(f"{API_URL}/trending-topics")
        print(f"   Thời gian: {time.time() - t0:.2f}s | Trạng thái HTTP: {res.status_code}")
        
        # Step 2: Generate Questions
        print(f"\n2. Tạo câu hỏi từ prompt: '{prompt[:50]}...'")
        t0 = time.time()
        res = await client.post(f"{API_URL}/generate-questions", json={"prompt": prompt})
        print(f"   Thời gian: {time.time() - t0:.2f}s | Trạng thái HTTP: {res.status_code}")
        data = res.json()
        if data.get("status") != "success":
            print(f"   LỖI API: {data.get('message')}")
            return False
        questions = data.get("questions", [])
        print(f"   Thành công! Đã sinh ra {len(questions)} câu hỏi.")
        
        # Mock answers
        answers = [f"Tôi muốn truyện mang phong cách nhẹ nhàng, tập trung vào nhân vật chính."] * len(questions)
        
        # Step 3: Refine Prompt
        print("\n3. Cô đọng ý tưởng (Refine Prompt)...")
        t0 = time.time()
        res = await client.post(f"{API_URL}/refine-prompt", json={
            "initial_prompt": prompt,
            "answers": answers,
            "questions": questions
        })
        print(f"   Thời gian: {time.time() - t0:.2f}s | Trạng thái HTTP: {res.status_code}")
        data = res.json()
        if data.get("status") != "success":
            print(f"   LỖI API: {data.get('message')}")
            return False
        refined = data.get("refined_prompt")
        print(f"   Thành công! Prompt đã tối ưu (độ dài {len(refined)} ký tự).")
        
        # Step 4: Generate Story (Streaming)
        print(f"\n4. Bắt đầu sinh truyện (Streaming) - Chế độ: {length}...")
        t0 = time.time()
        full_story = ""
        
        try:
            async with client.stream("POST", f"{API_URL}/generate-story", json={
                "refined_prompt": refined,
                "story_length": length
            }) as response:
                if response.status_code != 200:
                    text = await response.aread()
                    print(f"   LỖI HTTP {response.status_code}: {text.decode('utf-8')}")
                    return False
                
                print("   Đang nhận dữ liệu stream: [", end="", flush=True)
                chunk_count = 0
                async for chunk in response.aiter_text():
                    full_story += chunk
                    chunk_count += 1
                    if chunk_count % 5 == 0:
                        print(".", end="", flush=True)
                print("] Xong!")
        except Exception as e:
            print(f"\n   LỖI KẾT NỐI STREAM: {e}")
            return False
            
        elapsed = time.time() - t0
        word_count = len(full_story.split())
        print(f"   Thành công sinh truyện!")
        print(f"   Thời gian xử lý: {elapsed:.2f}s | Số từ (Tiếng Việt): {word_count}")
        print(f"   Tốc độ trung bình: {word_count / elapsed:.2f} từ/giây")
        
        snippet = " ".join(full_story.split()[:50])
        print(f"   Trích đoạn (50 từ đầu): {snippet}...")
        return True
        
async def main():
    print("BẮT ĐẦU KIỂM TRA TÍNH ỔN ĐỊNH VÀ HIỆU SUẤT API CHO MVP")
    
    cases = [
        {"name": "Truyện Chữa Lành (Ngắn)", "prompt": "Một cô gái bỏ việc ở thành phố, về một vùng quê hẻo lánh trồng rau nuôi cá để tìm lại sự bình yên.", "length": "short"},
        {"name": "Trùng Sinh Nữ Cường (Trung Bình)", "prompt": "Nữ chính sống lại quyết tâm trả thù những kẻ đã hãm hại mình kiếp trước bằng sự thông minh và mưu mô.", "length": "medium"}
    ]
    
    success_count = 0
    for i, case in enumerate(cases):
        success = await test_case(case["name"], case["prompt"], case["length"])
        if success:
            success_count += 1
            
        if i < len(cases) - 1:
            print("\n⏳ Nghỉ 20 giây để tránh giới hạn Rate Limit của Groq (Tier miễn phí)...")
            await asyncio.sleep(20)
            
    print(f"\n{'='*50}")
    print(f"KẾT QUẢ: {success_count}/{len(cases)} Test cases thành công.")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
