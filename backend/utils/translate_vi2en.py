"""
Vietnamese to English translation utility using deep-translator
"""

try:
    from deep_translator import GoogleTranslator

    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Warning: deep-translator not available, using fallback translation")


class Translation:
    """Translation utility using deep-translator or fallback"""

    def __init__(self):
        self.translator = None
        if TRANSLATION_AVAILABLE:
            try:
                self.translator = GoogleTranslator(source="vi", target="en")
                print("Google Translator initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Google Translator: {e}")
                self.translator = None

        # Fallback Vietnamese to English mappings for common words
        self.vi_to_en = {
            "người": "person",
            "xe": "car",
            "nhà": "house",
            "cây": "tree",
            "nước": "water",
            "trời": "sky",
            "mặt": "face",
            "tay": "hand",
            "chân": "leg",
            "mắt": "eye",
            "mũi": "nose",
            "miệng": "mouth",
            "tóc": "hair",
            "áo": "shirt",
            "quần": "pants",
            "giày": "shoes",
            "bàn": "table",
            "ghế": "chair",
            "sách": "book",
            "bút": "pen",
            "điện thoại": "phone",
            "máy tính": "computer",
            "tivi": "tv",
            "radio": "radio",
            "đồng hồ": "clock",
            "cửa": "door",
            "cửa sổ": "window",
            "tường": "wall",
            "sàn": "floor",
            "trần": "ceiling",
            "bếp": "kitchen",
            "phòng ngủ": "bedroom",
            "phòng tắm": "bathroom",
            "phòng khách": "living room",
            "nhà bếp": "kitchen",
            "vườn": "garden",
            "hoa": "flower",
            "cỏ": "grass",
            "đá": "stone",
            "cát": "sand",
            "biển": "sea",
            "sông": "river",
            "hồ": "lake",
            "núi": "mountain",
            "rừng": "forest",
            "đường": "road",
            "cầu": "bridge",
            "tàu": "ship",
            "máy bay": "airplane",
            "xe buýt": "bus",
            "xe máy": "motorcycle",
            "xe đạp": "bicycle",
            "tàu hỏa": "train",
            "xe taxi": "taxi",
            "xe tải": "truck",
            "xe cứu thương": "ambulance",
            "xe cảnh sát": "police car",
            "xe cứu hỏa": "fire truck",
            "xe cứu hộ": "rescue vehicle",
            "xe cứu trợ": "relief vehicle",
            "xe cứu nạn": "emergency vehicle",
            "xe cứu nguy": "emergency vehicle",
            "xe cứu cấp": "emergency vehicle",
            "ễ hội": "festival",
            "phía sau": "behind",
            "đàn ông": "man",
            "này": "this",
            "là": "is",
            "một": "a",
            "vật": "object",
            "trang trí": "decoration",
            "có": "has",
            "hình dáng": "shape",
            "con": "animal",
            "chim": "bird",
            "màu": "color",
            "tím": "purple",
            "và": "and",
            "trong": "in",
            "ngoài": "outside",
            "trên": "on",
            "dưới": "under",
            "bên": "side",
            "cạnh": "next to",
            "gần": "near",
            "xa": "far",
            "lớn": "big",
            "nhỏ": "small",
            "cao": "tall",
            "thấp": "short",
            "dài": "long",
            "ngắn": "short",
            "rộng": "wide",
            "hẹp": "narrow",
            "đẹp": "beautiful",
            "xấu": "ugly",
            "mới": "new",
            "cũ": "old",
            "sạch": "clean",
            "bẩn": "dirty",
            "nhanh": "fast",
            "chậm": "slow",
            "nóng": "hot",
            "lạnh": "cold",
            "ấm": "warm",
            "mát": "cool",
            "sáng": "bright",
            "tối": "dark",
            "trắng": "white",
            "đen": "black",
            "đỏ": "red",
            "xanh": "blue",
            "vàng": "yellow",
            "cam": "orange",
            "hồng": "pink",
            "nâu": "brown",
            "xám": "gray",
        }

    def __call__(self, text: str) -> str:
        """Translate Vietnamese text to English"""
        if not text:
            return text

        # Try using Google Translator first
        if self.translator:
            try:
                translated = self.translator.translate(text)
                print(f"Translated: '{text}' -> '{translated}'")
                return translated
            except Exception as e:
                print(f"Google translation failed: {e}, using fallback")

        # Fallback to dictionary-based translation
        return self._fallback_translate(text)

    def _fallback_translate(self, text: str) -> str:
        """Fallback translation using dictionary"""
        translated = text
        for vi_word, en_word in self.vi_to_en.items():
            translated = translated.replace(vi_word, en_word)

        print(f"Fallback translation: '{text}' -> '{translated}'")
        return translated

    def translate(self, text: str) -> str:
        """Alternative method for translation"""
        return self(text)
