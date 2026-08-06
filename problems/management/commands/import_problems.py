import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from problems.models import Problem, Tag

DEFAULT_CSV = Path(settings.BASE_DIR) / "leetcode_free_problems.csv"


class Command(BaseCommand):
    help = "匯入 leetcode_free_problems.csv 到資料庫（可重複執行，會 update_or_create）"

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(DEFAULT_CSV), help="CSV 檔案路徑")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"找不到檔案：{csv_path}"))
            return

        tag_cache = {}
        created, updated = 0, 0

        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                problem, was_created = Problem.objects.update_or_create(
                    number=int(row["題號"]),
                    defaults={
                        "title": row["題名"],
                        "title_slug": slugify(row["題名"]),
                        "url": row["網址"],
                        "difficulty": row["難度"],
                        "ac_rate": row["通過率(%)"],
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

                tag_names = [t for t in row["標籤"].split("|") if t]
                tag_objs = []
                for name in tag_names:
                    if name not in tag_cache:
                        tag_cache[name], _ = Tag.objects.get_or_create(
                            name=name, defaults={"slug": slugify(name)}
                        )
                    tag_objs.append(tag_cache[name])
                problem.tags.set(tag_objs)

        self.stdout.write(
            self.style.SUCCESS(
                f"完成：新增 {created} 題，更新 {updated} 題，共 {Problem.objects.count()} 題，"
                f"{Tag.objects.count()} 個標籤"
            )
        )
