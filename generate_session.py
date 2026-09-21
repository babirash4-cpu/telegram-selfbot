"""
اسکریپت اختصاصی و ایمن تولید Session String برای پایروگرام (Pyrogram)
کاملاً لوکال و بدون هیچ‌گونه نشت اطلاعات به سرورهای ناشناس
"""
import asyncio
from pyrogram import Client

async def main():
    print("=" * 60)
    print("🔐 ابزار تولید Session String سلف بات تلگرام (کاملاً امن و محلی)")
    print("=" * 60)
    
    api_id_input = input("👉 لطفاً API_ID خود را وارد کنید: ").strip()
    api_hash_input = input("👉 لطفاً API_HASH خود را وارد کنید: ").strip()

    if not api_id_input or not api_hash_input:
        print("❌ خطا: مقادیر وارد شده نامعتبر هستند.")
        return

    try:
        api_id = int(api_id_input)
    except ValueError:
        print("❌ خطا: API_ID باید یک عدد باشد.")
        return

    print("\n⏳ در حال اتصال به سرورهای تلگرام...")
    async with Client(name="session_gen", api_id=api_id, api_hash=api_hash_input, in_memory=True) as app:
        session_string = await app.export_session_string()
        me = await app.get_me()

        print("\n" + "=" * 60)
        print(f"🎉 تبریک! سشن استرینگ اکانت [{me.first_name}] با موفقیت تولید شد:")
        print("=" * 60)
        print("\n" + session_string + "\n")
        print("=" * 60)
        print(f"📌 آیدی عددی شما (OWNER_ID): {me.id}")
        print("💡 این مقدار را کپی کرده و در متغیر SESSION_STRING در فایل .env یا Railway قرار دهید.")
        print("⚠️ توجه: این سشن دسترسی کامل به اکانت شماست؛ آن را در اختیار افراد غریبه نگذارید!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
