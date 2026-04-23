import logging
from pathlib import Path

from PIL import Image

from sangpye_skill.constants import IMAGE_SIZE

logger = logging.getLogger(__name__)

# 13섹션 정의: 감정 여정 기반 고전환 상세페이지
SECTIONS = [
    {"number": 1,  "name": "01_hero",      "label": "Hero (긴급성 헤더)",        "height": 1600},
    {"number": 2,  "name": "02_pain",      "label": "Pain (공감)",                "height": 800},
    {"number": 3,  "name": "03_problem",   "label": "Problem (문제 정의)",        "height": 800},
    {"number": 4,  "name": "04_story",     "label": "Story (Before→After)",        "height": 1200},
    {"number": 5,  "name": "05_solution",  "label": "Solution (솔루션 소개)",      "height": 800},
    {"number": 6,  "name": "06_how",       "label": "How It Works (작동 방식)",    "height": 900},
    {"number": 7,  "name": "07_proof",     "label": "Social Proof (사회적 증거)",  "height": 1420},
    {"number": 8,  "name": "08_authority", "label": "Authority (권위/전문성)",    "height": 800},
    {"number": 9,  "name": "09_benefits",  "label": "Benefits (혜택)",             "height": 1200},
    {"number": 10, "name": "10_risk",      "label": "Risk Removal (리스크 제거)",  "height": 800},
    {"number": 11, "name": "11_compare",   "label": "Before/After Final (최종 대비)", "height": 800},
    {"number": 12, "name": "12_filter",    "label": "Target Filter (타겟 필터)",   "height": 700},
    {"number": 13, "name": "13_cta",       "label": "Final CTA (최종 CTA)",       "height": 900},
]

WIDTH = IMAGE_SIZE  # 1080
TOTAL_HEIGHT = sum(s["height"] for s in SECTIONS)  # 7500


class ComposerService:
    def __init__(self):
        self.width = WIDTH

    def resize_section(self, img: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """이미지를 지정된 크기로 리사이즈한다. 비율 유지 + 중앙 크롭."""
        w, h = img.size

        if w == target_width and h == target_height:
            return img

        # 비율 유지하며 커버하도록 스케일링
        scale = max(target_width / w, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # 중앙 크롭
        left = (new_w - target_width) // 2
        top = (new_h - target_height) // 2
        img = img.crop((left, top, left + target_width, top + target_height))

        return img

    def save_section(self, img: Image.Image, section_dir: Path, index: int) -> Path:
        """개별 섹션 이미지를 저장한다. 섹션별 높이에 맞게 리사이즈."""
        section_dir.mkdir(parents=True, exist_ok=True)

        section = SECTIONS[index] if index < len(SECTIONS) else {
            "name": f"{index + 1:02d}_section",
            "height": 600,
        }
        name = section["name"]
        target_height = section["height"]

        path = section_dir / f"{name}.png"
        img = self.resize_section(img, self.width, target_height)
        img.save(path, "PNG", quality=95)
        logger.info(f"섹션 저장: {path.name} ({img.size[0]}x{img.size[1]})")
        return path

    def compose_vertical(self, image_paths: list[Path], output_path: Path) -> Path:
        """13장의 이미지를 세로로 이어붙인다. 각 섹션은 고유 높이를 가진다."""
        images: list[Image.Image] = []
        total_height = 0

        for i, p in enumerate(image_paths):
            section = SECTIONS[i] if i < len(SECTIONS) else {"height": 600}
            target_height = section["height"]

            if p.exists():
                img = Image.open(p).convert("RGB")
                img = self.resize_section(img, self.width, target_height)
            else:
                # 누락된 이미지는 플레이스홀더로 대체
                img = Image.new("RGB", (self.width, target_height), (40, 40, 40))
                logger.warning(f"누락된 이미지 플레이스홀더: {p.name}")

            images.append(img)
            total_height += target_height

        if not images:
            raise ValueError("합성할 이미지가 없습니다.")

        # 세로로 이어붙이기
        combined = Image.new("RGB", (self.width, total_height))

        y_offset = 0
        for img in images:
            combined.paste(img, (0, y_offset))
            y_offset += img.size[1]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.save(output_path, "PNG", quality=95)
        logger.info(
            f"합성 완료: {output_path.name} ({combined.size[0]}x{combined.size[1]})"
        )
        return output_path
