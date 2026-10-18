# ابزارهای سبک مخزن

Python **3.11+** و کتابخانهٔ استاندارد کافی است. فرمان‌ها از ریشهٔ مخزن اجرا شوند؛
نصب package، backend یا محیط سرویس لازم نیست.

```sh
python3 scripts/atlas.py check
python3 -m unittest discover -s scripts/tests -v
```

`check` با خروجی `PASS` و exit code صفر موفق است؛ خطاها `FAIL` و exit code یک
دارند. تعداد تیکت، وجود عنوان یا عبور این فرمان کیفیت factual/editorial را ثابت
نمی‌کند. آزمون‌ها دادهٔ صریحاً مصنوعی را در پوشهٔ موقت می‌سازند و پاک می‌کنند؛
آنها در فهرست یا پوشهٔ محتوای واقعی ثبت نمی‌شوند.

## فهرست‌های تولیدی

پس از تغییر catalog یا دادهٔ قابل توزیع taxonomy:

```sh
python3 scripts/atlas.py generate
python3 scripts/atlas.py check
```

تنها `CONTENTS.md`, `PROGRESS.md`, `taxonomy/isic-rev5/INDEX.md` بازنویسی می‌شوند.
این نماها را دستی ویرایش نکنید. generate داده را معتبر اعلام نمی‌کند؛ check
دروازهٔ ساختاری است. موعد مرورِ گذشته در نمای پیشرفت ظاهر می‌شود؛ با رسیدن موعد
ممکن است نیاز به generate دوباره باشد. وضعیت published خودکار عوض نمی‌شود؛ انسان
باید اثر کهنگی را بررسی و وضعیت مناسب را ثبت کند.

## audit محلیِ فایل رسمی ISIC

سیاست پروژه commit دادهٔ کامل را تا احراز اجازهٔ بازنشر مجاز نمی‌داند. فایل خام
قبلاً در `fc6e5ac` روی main عمومی ثبت شده بود؛ اصلاح فعلی آن را فقط از index
برمی‌دارد، نسخهٔ محلی را حفظ می‌کند و تاریخچه را پاک نمی‌کند. جزئیات در
[یادداشت منبع](../sources/isic-rev5-research.md) است. فقط برای بررسی محلیِ
فایل رسمی، دانلود به مسیر ignored و audit زیر ممکن است. این فرمان‌ها را در محیطی
با دسترسی اینترنت اجرا کنید؛ منبع snapshot عوض شود، checksum عمداً خطا می‌دهد.

```sh
python3 - <<'PY'
import json
from pathlib import Path
from urllib.request import Request, urlopen

manifest = json.loads(Path('taxonomy/isic-rev5/manifest.json').read_text())
target = Path('.scratch/taxonomy/isic-rev5-source.csv')
target.parent.mkdir(parents=True, exist_ok=True)
request = Request(manifest['source_url'], headers={'User-Agent': 'BusinessAtlas-source-audit/1.0'})
with urlopen(request, timeout=60) as response:
    target.write_bytes(response.read())
print(target)
PY
python3 scripts/atlas.py audit-isic .scratch/taxonomy/isic-rev5-source.csv
python3 scripts/atlas.py check --local-taxonomy .scratch/taxonomy/isic-rev5-source.csv
```

audit اندازه و SHA256 snapshot، encoding، عنوان‌های اصلی بدون نرمال‌سازی،
کدهای یکتا، تعداد سطح و parent/order را می‌سنجد. چیزی نمی‌نویسد و پوشش عمومی را
عوض نمی‌کند. در این snapshot division زیر آخرین section، group زیر پیشوند
دورقمی و class زیر پیشوند سه‌رقمی بازیابی می‌شود. بدون hash مورد انتظار، این
استنتاج برای فایل دلخواه مجاز نیست.

`check --local-taxonomy` کدهای رکوردهای آینده را با همان audit بررسی می‌کند؛
check عادی فقط دادهٔ توزیع‌شده را می‌شناسد و نگاشت ناشناخته را رد می‌کند. این
تفاوت را در گزارش validation بنویسید. فایل را از `.scratch` به Git منتقل نکنید؛
برای توزیع عمومی، شاهد حقوق و import جداگانه لازم است.

قاعدهٔ ignore فقط `/.scratch/taxonomy/isic-rev5-source.csv` است؛ tracker محلیِ
Markdown قابل ثبت می‌ماند. `check` در checkout دارای `.git`، index را با Git
می‌سنجد و حتی `git add -f` این فایل را رد می‌کند. در archive بدون `.git`، index
وجود ندارد و این بررسی انجام نمی‌شود؛ این حفاظت hook یا پاک‌کنندهٔ تاریخچه نیست.

## hash انتشار

```sh
python3 scripts/atlas.py hash templates/business-chapter.md
```

فرمان برای هر مسیر واقعی فایل SHA256 می‌دهد؛ مسیر بالا فقط نمایش کارکرد است،
نه تأیید قالب به عنوان فصل. برای یک رکورد واقعیِ موجود، فرمان
`python3 scripts/atlas.py revision-hash RECORD_ID` hash نسخهٔ مادی می‌دهد؛
`RECORD_ID` را با شناسهٔ واقعی catalog جایگزین کنید. این مخزن هنوز رکورد ندارد.
دو hash متن و نسخه، شاهد مرور و اجازهٔ واقعی انسان در publication ثبت می‌شوند؛
[قرارداد دقیق](../docs/editorial.md) تغییر مادیِ دامنه، فعالیت، رابطه و شاهد را
به مرور دوباره متصل می‌کند. ابزار هویت تأییدکننده را احراز نمی‌کند.

## مرز بررسی و موارد مؤخر

بررسی‌ها: فایل‌های لازم، ساختار JSON، شناسه/مسیر تکراری و رکورد بدون ثبت، نوع
رابطه، namespace و کد طبقه‌بندیِ در دسترس، وضعیت‌ها، ترجمه و منشأ، منابع و
ارجاع ناشناخته، ۲۶ تصمیم پوشش و نشانه‌های انتشار، hash و اطلاعات مرور، پیوندهای
نسبی/anchor و سازگاری نماهای تولیدی. قلمرو Markdown پروژه است؛ مهارت‌های نصب‌شده
و `.scratch` اسکن نمی‌شوند. پیوندهای خارجی زنده خودکار بررسی نمی‌شوند.

سبک پیوند پشتیبانی‌شده: inline Markdown و anchor صریح HTML یا heading معمولی؛
برای هدف محلی فاصله در مسیر استفاده نکنید. reference-style link و headingهای
پیچیدهٔ وابسته به renderer فعلاً خارج قراردادند. ساختار متن نمی‌تواند کفایت
شاهد، مجوز حقوقی یا صحت محاسبهٔ اقتصادی را تضمین کند.

CI پیچیده، renderer کتاب، schema library، موتور جست‌وجو و بررسی خودکار حقیقت
به دلیل نبود محتوای واقعی و هزینهٔ نگه‌داری مؤخرند. اگر parser دیگری اضافه شد،
قرارداد و fixtures آن نیز باید به‌روز شوند.
