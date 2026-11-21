# Cermin Murah yang "Mempercepat" Lift — 2.5D/3D Blender YouTube Shorts Pipeline

Proyek animasi vertikal YouTube Shorts (**9:16, 1080×1920, 30 FPS, ~61 detik**) bergaya **2.5D Stylized Pill/Capsule Cutout Characters + True 3D Art Deco Handheld Props inside a Blender 3D Art Deco Lobby**, dibangun 100% secara terprogram menggunakan Python (`bpy`, SVG→PNG, `edge-tts`, DSP Foley/BGM, FFmpeg) dan dirancang untuk dirender otomatis **tanpa membuka GUI Blender** melalui **GitHub Actions (10-way parallel matrix)**.

---

## Struktur Repositori

```text
├── .github/workflows/
│   └── blender-pipeline.yml        # Workflow GitHub Actions headless (prepare -> 10x parallel render -> compose)
├── scripts/
│   ├── storyboard.py               # Single source of truth 10 scene (narasi, mood, SFX cues)
│   ├── render_preview.py           # Renderer 4 screenshot preview 9:16 (Gate 3)
│   ├── render_final.py             # Renderer animasi penuh per scene (Stage 4 / parallel matrix)
│   ├── compose.py                  # FFmpeg concat + audio mix + burn-in pop-in ASS subtitles -> MP4
│   ├── characters/
│   │   ├── svg_core.py             # Shading cel-PBR & variable-width organic ink outlines
│   │   ├── rig.py                  # Biomechanical 2-Bone IK stick limbs, hands & 3D shoes
│   │   ├── expressions.py          # Swappable facial expression engine (6 ekspresi/karakter)
│   │   ├── props.py                # Properti 2D untuk lembar Character Sheet
│   │   ├── cast.py                 # 4 karakter utama (Raka, Pak Bima, Pak Doni, Clara)
│   │   ├── turnaround.py           # Sistem rotasi 5 sudut (0°, 45°, 90°, 135°, 180°)
│   │   └── generate_characters.py  # Ekspor sprite transparan (SVG/PNG) + manifest.json + sheets
│   ├── blender/
│   │   ├── compat.py               # Kompatibilitas Blender 4.2 LTS / 4.5 / 5.x (EEVEE Next + Cycles + Freestyle)
│   │   ├── materials.py            # Library material Stylized Toon-PBR Art Deco
│   │   ├── environment.py          # Lobi Gedung Art Deco 3D (lift, dial, jam raksasa, cermin, roket)
│   │   ├── props_3d.py             # 9 properti tangan 3D Art Deco yang menyatu di tangan karakter
│   │   ├── lighting.py             # 3 mood pencahayaan (morning_busy, midday_stress, golden_mirror)
│   │   ├── characters_3d.py        # Loader kartu 2.5D + alpha-cutout shadow + double-sided mirror card
│   │   ├── anim_utils.py           # Kamera Bezier, squash-and-stretch, swap ekspresi, animasi jam/lift
│   │   └── scenes.py               # Koreografi lengkap 10 scene (00:00 – 01:01)
│   └── audio/
│       └── generate_audio.py       # Narasi Indonesia (edge-tts) + Foley SFX + BGM Jazz Art Deco + ASS subtitles
├── assets/characters/              # Sprite transparan & manifest.json
├── previews/                       # Character Sheet, Turnaround Sheet & 4 screenshot 3D (Gate 2 & 3)
├── STORYBOARD.md                   # Storyboard shot-by-shot ber-timestamp
└── requirements.txt
```

---

## Cara Render Video Final di GitHub Actions (Tanpa Buka Blender!)

1. **Inisialisasi & Push ke GitHub:**
   ```bash
   git init
   git add .
   git commit -m "feat: complete 2.5D/3D Blender Art Deco YouTube Shorts pipeline"
   git branch -M main
   git remote add origin https://github.com/<USERNAME>/<REPO_NAME>.git
   git push -u origin main
   ```
2. **Jalankan Workflow di GitHub:**
   - Buka repositori di GitHub → klik tab **Actions**.
   - Pilih workflow **`Blender 2.5D Animation Pipeline`** di sidebar kiri.
   - Klik tombol **`Run workflow`** lalu pilih:
     - `mode`: **`final`**
     - `quality`: **`production`** (`1080×1920`, 16 samples EEVEE + Freestyle) — atau `draft_fast` (`720×1280`, 8 samples) untuk uji super cepat.
     - `engine`: **`eevee`** (disarankan untuk kecepatan cloud CI; atau `cycles` untuk refleksi raytraced penuh).
3. **Unduh Video Final (`output_short_9x16.mp4`):**
   - Pipeline otomatis menjalankan **10 runner Blender Linux secara paralel** (1 runner per scene), lalu menggabungkan seluruh klip + audio + subtitle lewat FFmpeg.
   - Setelah job `compose-final` berstatus hijau, gulir ke bagian **Artifacts** dan unduh **`youtube-short-9x16-final`** (`output_short_9x16.mp4`).

---

## Cara Jalankan Secara Lokal (Opsional, CLI Headless)

```bash
pip install -r requirements.txt
python scripts/characters/generate_characters.py
python scripts/audio/generate_audio.py
blender -b --python-exit-code 1 --python scripts/render_final.py -- --scene all --engine eevee --samples 16 --encode-clip
python scripts/compose.py
```
