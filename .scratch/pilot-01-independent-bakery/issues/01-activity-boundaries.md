# شواهد مرز فعالیت‌های تولید، فروش و خدمت در نانوایی

Type: research
Label: wayfinder:research
Status: resolved
Assigned: Codex/bakery_activity_research
Parent: ../map.md
Blocked by:

## Question

در ISIC Rev.5، توضیحات شمول/عدم‌شمول و اصلاحیهٔ جاری چه تمایزی میان تولید نان و محصولات پختنی، تولید همراه فروش مستقیم، فروش محصول تولید دیگران، تأمین عمده و تهیه/ارائه برای مصرف فوری می‌گذارند؟ چه قواعدی برای واحد چندفعالیتی و فعالیت اصلی/فرعی مرتبط است و از این طبقه‌بندی چه چیزی دربارهٔ مرز گونه یا «مستقل» نمی‌توان نتیجه گرفت؟

پژوهش فقط برای تصمیم دامنه است: منابع رسمی UNSD، محل دقیق شاهد، تاریخ/نسخه، وضعیت دسترسی و موارد نامعلوم ثبت شوند. سناریوهای مقایسه صریحاً فرضی‌اند؛ آماری یا قاعده‌ای دربارهٔ همهٔ نانوایی‌ها ساخته نشود. فایل ساختار محلی طبق scripts/README.md audit شود؛ ساختار به‌تنهایی شاهد شمول نیست. دادهٔ محدود بازنشر نشود.

خروجی یک یادداشت اصیل فارسی با اصطلاحات انگلیسی و ارجاع نزدیک ادعاست؛ روی شاخهٔ موقت `research/pilot-01-bakery-activity-boundaries`، بدون PR یا merge، با commit/path به عنوان context pointer. اگر دریافت، push یا سند قابل اتکا ممکن نشد، مانع واقعی ثبت شود. نتیجه نگاشت نهایی فهرست را خودکار تعیین نمی‌کند.

## Dependencies

نتیجه برای [انتخاب نقطهٔ مرجع آموزشی فصل نانوایی مستقل](02-chapter-reference.md) و [تعیین معیار شمول و معنای مستقل در گونهٔ نانوایی](03-archetype-boundary.md) ورودی است.

## Answer

پژوهش AFK در 2026-10-18 با منابع رسمی UNSD تکمیل شد؛ انتخاب آموزشی یا مرز گونه تصویب نشد. تفکیک مستند تولید، بازفروش خرده/عمده و خدمت مصرف فوری، استثنای تولید همراه فروش همان واحد، واحد محلی/بنگاه و اصلی/ثانویه/پشتیبان، در جدول شاهد یادداشت آمده است. وضعیت نیم‌پخت بدون اطلاعات عملیات واقعی باز است؛ این شکاف مانع استفاده از شواهد روشن برای تصمیم آموزشی نیست. معنای «مستقل» همچنان تصمیم انسانی است.

Context pointer: [یادداشت شواهد مرز فعالیت نانوایی](https://github.com/h3nrzi/the-business-atlas/blob/2bf232d6f36b096d772f74cbc90ba23f132770c1/docs/research-notes/pilot-01-bakery-activity-boundaries.md)؛ commit `2bf232d6f36b096d772f74cbc90ba23f132770c1`، مسیر `docs/research-notes/pilot-01-bakery-activity-boundaries.md`، شاخهٔ `research/pilot-01-bakery-activity-boundaries` (از HEAD ریشهٔ `db5c9d0` در worktree جدا). push موفق؛ PR و merge انجام نشد. یادداشت فعلاً فقط روی شاخهٔ پژوهش است و انتقال آیندهٔ دانش پایدار نیازمند بازبینی است.

منابع: [راهنمای White-cover 2026](https://unstats.un.org/unsd/classifications/Econ/Download/ISIC_Rev5_Publication-white_cover_version.pdf) [@src-un-isic5-manual] و [اصلاحیهٔ 17 August 2026](https://unstats.un.org/unsd/classifications/Econ/Download/Errata_for_the_Explanatory_Notes_of_the_ISICRev5_-_2026.pdf) [@src-un-isic5-errata]؛ صفحه/کلاس دقیق و hash دریافت در یادداشت ثبت است. هیچ منبع یا دادهٔ محدود جدید به root اضافه نشد.

پیش‌پرواز واقعی از ریشه: `audit-isic` و `check --local-taxonomy` هر دو PASS و exit صفر؛ 830 کد یکتا و صفر خطای parent/order با SHA256 مورد انتظار snapshot. در worktree پژوهش نیز `python3 scripts/atlas.py check` PASS؛ commit فقط یک Markdown دارد. دادهٔ CSV/PDF commit نشد. مانع دریافت/دسترسی/push باقی نماند. این‌ها صحت ساختاری و قابلیت بازبینی را نشان می‌دهند؛ پذیرش انسانی دامنه یا انتشار فصل نیستند.

اقدام بعدی: گفت‌وگوی HITL در [انتخاب نقطهٔ مرجع آموزشی فصل نانوایی مستقل](02-chapter-reference.md)، با حفظ پرسش مرز گونه برای تیکت مربوط.
