# گزارش پذیرش زیرساخت مخزن

تاریخ: 2026-10-18. مشخصات مبنا: درخواست «Repository Infrastructure Implementation»
مالک پروژه در همین جلسه؛ خلاصهٔ محلی در `.scratch/repository-infrastructure/spec.md`.
مبنای Git پیش از کار: `511c0c8`. این گزارش ارزیابی زیرساخت است؛ هیچ فصل یا
بررسی کسب‌وکار آغاز نشده است. ارزیابی hands-on انسان **pending / not_run** است.

## بازرسی اولیه

شاخه `main`، remote برابر `https://github.com/h3nrzi/the-business-atlas.git`،
working tree تمیز بود. README کوتاه، AGENTS، سه سند `docs/agents/`، ۳۸ مهارت
نصب‌شده با ۱۰۳ فایل و `skills-lock.json` وجود داشتند. tracker محلی با نقش‌های
triage و اجرای مستقل claimed/resolved Wayfinder تأیید شد. مهارت‌های writing-for-agents،
domain-modeling و Wayfinder واقعی خوانده شدند؛ هیچ‌یک بازنویسی یا نصب مجدد نشدند.

## نگاشت پذیرش به شاهد

| گروه معیار | وضعیت | شاهد و محدودیت |
| --- | --- | --- |
| سازگاری مهارت‌ها و tracker | pass | diff مهارت‌ها، lockfile و سه سند agent باید خالی باشد؛ AGENTS فقط pointer اضافه دارد |
| منشور، هویت و دامنه | pass | [منشور](charter.md)، [README](../README.md)، واژگان دو زبان؛ تحلیل کسب‌وکار اولویت اصلی |
| معماری و هویت پایدار | pass | [قرارداد](architecture.md)، catalog واحد و خالی، رابطه‌های نوع‌دار و مرز فعالیت/گونه/مدل/درآمد |
| ساختار فصل و نرم‌افزار | pass | [۲۶ بُعد](../templates/business-chapter.md) با هدف، پرسش، عمق، شاهد، نمایش و معیار؛ [مکمل نیاز](../templates/software-analysis.md) |
| منابع، provenance، حقوق و اصلاح | pass | [روش](research.md)، رجیستری منابع و قالب ادعا، گزارش ISIC؛ مجوز محتوای تألیفی هنوز انتخاب نشده |
| یادگیری و سنجش مستقل | pass | [استاندارد](learning.md)، تمرین سه سطح و یادداشت شخصی؛ انتشار دلیل تسلط نیست |
| مراحل و اختیار انتشار | pass | [تحریریه](editorial.md)، تأیید انسانیِ نسخه و hash، حفظ تاریخچه و بازگشت به review |
| طبقه‌بندی توزیع‌پذیر و پیمایش کامل | **partial** | تمام ۸۳۰ رکورد غایب‌اند؛ حقوق بازنشر احراز نشده. [manifest](../taxonomy/isic-rev5/manifest.json) و index این کمبود را نشان می‌دهند |
| بررسی کامل منبع رسمی | pass | ۸۳۰ کد یکتا، ۲۲/۸۷/۲۵۸/۴۶۳، صفر خطای hierarchy؛ اندازه و checksum مشخص؛ برچسب‌ها بدون تغییر فقط محلی خوانده شدند |
| Wayfinder واقعی و مرز artifacts | pass | [راهنما](workflows/wayfinder.md)، planning پیش‌فرض، HITL واقعی، claim/block/resolve و ادامه/تحویل؛ فراخوانی نمونه اجرا نشده |
| tracker جهانی و ناوبری کتاب | pass | [فهرست](../CONTENTS.md)، [پیشرفت](../PROGRESS.md) از catalog؛ صفر فصل و مخرج جهانی نامعلوم |
| validation و محدودیتش | pass | [ابزار](../scripts/README.md)، fixtures موقت؛ ساختار با کیفیت محتوا یکی نیست |
| حفاظت دامنه | pass | بدون فصل واقعی، CMS، backend، LMS، محصول وب یا taxonomy موازی |
| تأیید انسانی زیرساخت | pending | راهنمای محلی acceptance آماده است؛ فقط مشاهدهٔ واقعی انسان نتیجه را تغییر می‌دهد |

«pass» در جدول یعنی بررسی اجرایی/مستند در این پیاده‌سازی؛ امضای انسانی انتشار
یا ارزیابی واقعی یادگیرنده محسوب نمی‌شود. fallback واردسازی ناقصِ شفاف رعایت
شده است؛ **واردسازی کامل عمومی انجام نشده و ادعا نمی‌شود**.

## شواهد فرمان‌ها

نتیجهٔ واقعی روی Python 3.14.7 در 2026-10-18:

| فرمان/بررسی | نتیجه |
| --- | --- |
| `generate` و سپس `check` | pass؛ سه نمای تولیدی سازگار، پیوند و anchor داخلی معتبر |
| `audit-isic` روی snapshot رسمی محلی | pass؛ ۸۳۰ کد یکتا، ۲۲/۸۷/۲۵۸/۴۶۳، صفر خطای parent/order |
| `check --local-taxonomy` | pass؛ فایل با checksum مورد انتظار خوانده شد |
| `python3 -m unittest discover -s scripts/tests -v` | pass؛ ۲۲ آزمون، شامل دو regression از بازبینی |
| `git diff --check` | pass؛ بدون خطای whitespace |
| diff مهارت‌ها، lockfile و `docs/agents/` نسبت به `511c0c8` | خالی؛ بدون تغییر |
| preflight CLI در کپی موقت | PASS عادی؛ stale index با exit 1؛ generate و بازیابی با exit 0؛ duplicate ID و CSV تغییرکرده با exit 1؛ کپی پاک شد |

SHA256 منبع: `fc408f57bd3a4f33c35a4f384ec0010283dd72774892c8d48ae1330a8caeb57f`،
اندازه ۴۵۴۸۱ بایت. فرمان‌های تکرارپذیر:

```sh
python3 scripts/atlas.py generate
python3 scripts/atlas.py check
python3 scripts/atlas.py audit-isic .scratch/taxonomy/isic-rev5-source.csv
python3 scripts/atlas.py check --local-taxonomy .scratch/taxonomy/isic-rev5-source.csv
python3 -m unittest discover -s scripts/tests -v
git diff --check
git diff 511c0c8 -- .agents/skills skills-lock.json docs/agents
```

## محدودیت و ادامه

- **مانع داده:** اجازهٔ بازنشر/ترجمهٔ hierarchy احراز نشده است. صاحب پروژه می‌تواند
  مجوز اختصاصی یا اجازهٔ کتبی مناسب تهیه کند؛ در این جلسه ارتباطی با UN برقرار نشد.
  تا آن زمان کدهای آینده فقط با source audit محلی قابل بررسی‌اند و نماهای عمومی
  hierarchy کامل ندارند.
- **تصمیم باز:** مجوز عمومی برای آثار تألیفی انتخاب نشده است؛ مخزن مجوز باز ادعا نمی‌کند.
- **مرز ابزار:** تحلیل درست، کفایت ادعا، اختیار شخص امضاکننده، روابط اقتصادی واقعی
  و حق استفاده از هر اثر به بازبینی انسانی نیاز دارند؛ لینک خارجی خودکار ping نمی‌شود.
- **مؤخرِ عمدی:** انتشار وب/کتاب، crosswalk، ثبت شخصی یادگیری و اتوماسیون CI؛ اینها
  مانع استفادهٔ Markdown نیستند.

نقطهٔ شروع بررسی نخست: مالک گونه را انتخاب کند، [راهنمای Wayfinder](workflows/wayfinder.md)
و متن نمونه را بخواند، هویت تکراری را بررسی کند و مقصد planning را با انسان روشن
کند. در این تحویل نه موضوعی انتخاب شده و نه پژوهش کسب‌وکاری شروع شده است.

## بازبینی تغییر

مبنای بازبینی `511c0c8` و commit پیاده‌سازی `9e9f27a` است. طبق مهارت نصب‌شدهٔ
code-review دو محور مستقل بررسی شدند:

- **Standards:** دو یافته؛ ارجاع منبعِ companion می‌توانست از اعلام منبع در رکورد
  عبور کند و یادداشت ISIC marker استاندارد نداشت. هر دو رفع شدند؛ برای companion
  و سند review دو regression اضافه شد. بازبین رفع را تأیید کرد و ۲۲ آزمون را اجرا کرد.
- **Spec:** نقص اجرایی اضافه یا scope creep پیدا نشد؛ ناقص‌بودن آگاهانهٔ taxonomy
  همان fallback مجاز و مستند است. بالاترین نقص Standards پیش از رفع P2 بود؛ نقص
  باقی‌مانده در بازبینی هدفمند یافت نشد.

در طول کار commit هم‌زمانِ مالک، `fc6e5ac`، روی main و remote ظاهر شد و فایل خام
ISIC و اسناد محلی را به Git افزود. این تغییر متعلق به این پیاده‌سازی نیست و حذف،
بازنویسی یا force-push نشده است. برای حفظ مرز تغییر، push نهایی زیرساخت روی شاخهٔ
`infrastructure-foundation` از `9e9f27a` و اصلاحات scoped انجام می‌شود؛ commit مالک
در تاریخچهٔ این شاخه وارد نمی‌شود. اعداد «توزیع‌شده» این گزارش به دادهٔ canonical
و artifact همین شاخه اشاره دارند؛ وجود فایل در commit مستقل مالک مجوز حقوقی ایجاد
نمی‌کند و وضعیت canonical را complete نمی‌کند.

## ارزیابی hands-on

مهارت سراسری ticket-walkthrough پس از بررسی‌ها و بازبینی اعمال شد. راهنمای محلی:
`.scratch/repository-infrastructure/acceptance/01-foundations/guide.md`، با پوشش
معیارها، اقدام قابل تکرار، preflight واقعی و checkpoint. نتایج انسان همه `not_run`
هستند. این راهنما gate تازه‌ای برای تکمیل پیاده‌سازی نیست.
