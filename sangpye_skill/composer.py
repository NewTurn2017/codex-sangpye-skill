import logging
from pathlib import Path

from PIL import Image, ImageDraw

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

    @staticmethod
    def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
        """카드 모서리를 둥글게 깎는 알파 마스크를 만든다."""
        w, h = size
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
        return m

    def compose_cards(
        self,
        image_paths: list[Path],
        output_path: Path,
        *,
        side: int = 30,
        gap: int = 40,
        pad: int = 40,
        radius: int = 24,
        bg: str = "#0B1020",
    ) -> Path:
        """13장의 섹션을 '카드형'으로 합성한다.

        compose_vertical()이 섹션을 간격 0으로 풀블리드로 이어붙이는 것과 달리,
        통일된 다크 배경 위에 각 섹션을 둥근 모서리 카드로 얹고 일정한 여백(좌우 side,
        카드 사이 gap, 상/하단 pad)을 둔다. 섹션 경계에서 배경색이 급전환되는 현상을
        없애 '카드 리듬'으로 정리하는 게 목적이다. 강의 상세페이지처럼 통일감이 필요한
        콘텐츠에 어울린다. (제품 풀블리드 상폐는 compose_vertical을 그대로 쓴다.)

        누락된 섹션은 SECTIONS의 정의 높이에 맞춘 다크 카드 플레이스홀더로 대체한다.
        """
        card_w = self.width - 2 * side
        if card_w <= 0:
            raise ValueError(f"side({side})가 너무 커서 카드 폭이 0 이하입니다.")

        cards: list[Image.Image] = []
        for i, p in enumerate(image_paths):
            section = SECTIONS[i] if i < len(SECTIONS) else {"height": 600}
            if p.exists():
                img = Image.open(p).convert("RGB")
                # 폭만 카드 폭에 맞추고 비율 유지(크롭 없음) — recompose_cards.py와 동일.
                if img.width != card_w:
                    new_h = round(img.height * card_w / img.width)
                    img = img.resize((card_w, new_h), Image.LANCZOS)
            else:
                placeholder_h = round(section["height"] * card_w / self.width)
                img = Image.new("RGB", (card_w, placeholder_h), (40, 40, 40))
                logger.warning(f"누락된 이미지 카드 플레이스홀더: {p.name}")
            img.putalpha(self._rounded_mask(img.size, radius))
            cards.append(img)

        if not cards:
            raise ValueError("합성할 이미지가 없습니다.")

        total_h = pad * 2 + sum(c.height for c in cards) + gap * (len(cards) - 1)
        canvas = Image.new("RGB", (self.width, total_h), bg)

        y = pad
        for c in cards:
            canvas.paste(c, (side, y), c)  # 알파(둥근 모서리) 마스크로 합성
            y += c.height + gap

        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "PNG", quality=95)
        logger.info(
            f"카드 합성 완료: {output_path.name} ({canvas.size[0]}x{canvas.size[1]}, "
            f"cards={len(cards)}, side={side}/gap={gap}/pad={pad}/radius={radius})"
        )
        return output_path
