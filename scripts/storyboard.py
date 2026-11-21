"""Single-source-of-truth 10-scene Storyboard for 'Cermin Murah yang Mempercepat Lift' (60s, 30 FPS, 9:16)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

FPS = 30
WIDTH = 1080
HEIGHT = 1920


@dataclass(frozen=True)
class SfxCue:
    offset_ratio: float  # 0.0..1.0 within scene duration
    sfx_type: str        # whoosh, click_burst, tick_slow, tick_fast, rocket_rev, thud, sip, chime_aha, mirror_drop, boing, sparkle, ding, door_slide, jazz_fin
    volume: float = 0.8


@dataclass(frozen=True)
class SceneSpec:
    scene_id: int
    slug: str
    title: str
    default_duration_s: float
    mood: str              # morning_busy | midday_stress | golden_mirror
    mirrors_on: bool
    rocket_on: bool
    narration: str
    camera_note: str
    visual_beat: str
    sfx_cues: Tuple[SfxCue, ...]


STORYBOARD: List[SceneSpec] = [
    SceneSpec(
        scene_id=1,
        slug="s01_hook_lobby",
        title="Hook: Gedung Hampir Bangkrut Gara-Gara Lift",
        default_duration_s=5.5,
        mood="morning_busy",
        mirrors_on=False,
        rocket_on=False,
        narration="Gedung pencakar langit ini hampir bangkrut—hanya gara-gara liftnya terlalu lambat!",
        camera_note="Foreground parallax melewati stanchion & palem → fast smooth Bezier push-in menuju lobi & Jam Raksasa.",
        visual_beat="Pak Doni murka di pintu lift kiri; Pak Bima panik menggoyang clipboard 3D Komplain 99%; Jam Raksasa berdetak berat.",
        sfx_cues=(
            SfxCue(0.02, "whoosh", 0.75),
            SfxCue(0.32, "tick_slow", 0.65),
            SfxCue(0.68, "thud", 0.55),
        ),
    ),
    SceneSpec(
        scene_id=2,
        slug="s02_angry_wait",
        title="Konflik: Penghuni Mengamuk & Memencet Tombol",
        default_duration_s=6.0,
        mood="midday_stress",
        mirrors_on=False,
        rocket_on=False,
        narration="Setiap pagi, penghuni mengamuk memelototi jam tangan... sambil menekan tombol lift berkali-kali!",
        camera_note="Whip-pan tajam ke close-up Pak Doni (3/4 furious) → tilt cepat ke jarum dial lantai yang merayap.",
        visual_beat="Mood berubah kontras merah-amber; Pak Doni melonjak marah dengan koper & jam 3D, tombol lift merah berkedip cepat, jarum dial bergerak super pelan.",
        sfx_cues=(
            SfxCue(0.04, "whoosh", 0.80),
            SfxCue(0.38, "click_burst", 0.90),
            SfxCue(0.72, "tick_slow", 0.75),
        ),
    ),
    SceneSpec(
        scene_id=3,
        slug="s03_rocket_plan",
        title="Komedi: Insinyur Mengusulkan Mesin Roket Turbo",
        default_duration_s=6.0,
        mood="midday_stress",
        mirrors_on=False,
        rocket_on=True,
        narration="Manajer gedung panik total! Para insinyur pun mengusulkan mesin roket turbo—yang biayanya miliaran!",
        camera_note="Crash zoom ke Pak Bima panik → whip-pan ke Clara meluncurkan kereta Roket Turbo 3D masuk ke lobi!",
        visual_beat="Pak Bima gemetar (panic -> shocked); Clara (excited -> determined) mendorong kereta roket 3D bergetar penuh semangat sambil mengangkat blueprint & kunci inggris 3D.",
        sfx_cues=(
            SfxCue(0.05, "whoosh", 0.70),
            SfxCue(0.38, "rocket_rev", 0.85),
            SfxCue(0.80, "thud", 0.80),
        ),
    ),
    SceneSpec(
        scene_id=4,
        slug="s04_chill_psychologist",
        title="Plot Twist: Psikolog Santai Menyeruput Kopi",
        default_duration_s=5.5,
        mood="midday_stress",
        mirrors_on=False,
        rocket_on=True,
        narration="Tapi anggaran mereka nol besar! Sampai seorang psikolog muda cuma menyeruput kopi dan berkata...",
        camera_note="Smooth foreground parallax dolly menyusuri kolom marmer menuju Raka yang tenang di tengah kekacauan.",
        visual_beat="Raka (deadpan -> chill) menyeruput gelas kopi Art Deco 3D dengan uap melengkung halus; Clara (confused) & Pak Bima (skeptical) melongo di latar belakang.",
        sfx_cues=(
            SfxCue(0.05, "boing", 0.65),
            SfxCue(0.55, "sip", 0.85),
        ),
    ),
    SceneSpec(
        scene_id=5,
        slug="s05_aha_brain",
        title="Momen Aha!: Masalahnya Bukan Mesin, Tapi Persepsi Otak",
        default_duration_s=5.8,
        mood="morning_busy",
        mirrors_on=False,
        rocket_on=False,
        narration="Masalahnya bukan mesin liftnya—melainkan persepsi otak kita saat menunggu tanpa distraksi!",
        camera_note="Low-angle hero close-up Raka (aha!) mengangkat cermin emas 3D → tilt dramatis ke Jam Mekanik Raksasa.",
        visual_beat="Raka tersenyum cerah (aha!) mengacungkan cermin tangan emas Art Deco 3D; di atasnya, jarum detik merah Jam Raksasa mundur elastis lalu berdetak lambat!",
        sfx_cues=(
            SfxCue(0.10, "chime_aha", 0.90),
            SfxCue(0.52, "tick_slow", 0.85),
            SfxCue(0.80, "tick_slow", 0.85),
        ),
    ),
    SceneSpec(
        scene_id=6,
        slug="s06_unoccupied_time",
        title="Analogi Visual 3D: 30 Detik Terasa Seperti 30 Menit",
        default_duration_s=5.8,
        mood="midday_stress",
        mirrors_on=False,
        rocket_on=False,
        narration="Saat menatap pintu besi polos, tiga puluh detik terasa seperti tiga puluh menit!",
        camera_note="Slow claustrophobic dolly push-in ke pintu lift polos & Pak Doni (impatient) di bawah Jam Raksasa.",
        visual_beat="Pak Doni berdiri bosan & kesal menatap pintu kuningan tertutup rapat sementara jarum detik Jam Raksasa di atasnya tersendat kaku seperti karet berat.",
        sfx_cues=(
            SfxCue(0.12, "tick_slow", 0.90),
            SfxCue(0.48, "tick_slow", 0.92),
            SfxCue(0.82, "tick_slow", 0.95),
        ),
    ),
    SceneSpec(
        scene_id=7,
        slug="s07_mirror_drop",
        title="Solusi Cerdas: Cermin Emas Murah Dipasang di Lobi!",
        default_duration_s=6.0,
        mood="golden_mirror",
        mirrors_on=True,
        rocket_on=False,
        narration="Jadi mereka tidak menyentuh mesinnya sama sekali! Mereka cuma menempel cermin murah di samping lift!",
        camera_note="Hero reveal tracking shot ke pilar tengah saat Cermin Emas Art Deco meluncur turun dari atas dengan pantulan pegas!",
        visual_beat="Cahaya berubah drastis ke Sore Emas + debu berkilau! Cermin Art Deco 3D jatuh mulus memantul ke dinding; Clara (shocked -> deadpan) helmnya terangkat kaget!",
        sfx_cues=(
            SfxCue(0.08, "whoosh", 0.85),
            SfxCue(0.36, "mirror_drop", 0.95),
            SfxCue(0.52, "sparkle", 0.90),
        ),
    ),
    SceneSpec(
        scene_id=8,
        slug="s08_mirror_narcissist",
        title="Komedi Puncak: Pak Doni Tercengang Lalu Narsis Bercermin!",
        default_duration_s=6.8,
        mood="golden_mirror",
        mirrors_on=True,
        rocket_on=False,
        narration="Seketika, penghuni yang tadinya marah—langsung lupa waktu gara-gara asyik merapikan rambut di cermin!",
        camera_note="Over-the-shoulder cinematic orbit di belakang Pak Doni (135°) menyorot pantulan 3D live di dalam cermin!",
        visual_beat="Di pantulan cermin 3D nyata, wajah Pak Doni berubah dari Tercengang (stunned) → Narsis berkilau (narcissistic) sambil mengayunkan sisir emas 3D menyisir jambul pompadournya!",
        sfx_cues=(
            SfxCue(0.14, "boing", 0.80),
            SfxCue(0.44, "sparkle", 0.95),
            SfxCue(0.76, "sparkle", 0.80),
        ),
    ),
    SceneSpec(
        scene_id=9,
        slug="s09_clock_fast_ding",
        title="Hasil Nyata: Jam Terasa 2x Lebih Cepat & Komplain Hilang 90%",
        default_duration_s=6.8,
        mood="golden_mirror",
        mirrors_on=True,
        rocket_on=False,
        narration="Kecepatan lift tetap sama persis—tapi jam terasa melesat dua kali lebih cepat, dan komplain turun sembilan puluh persen!",
        camera_note="Tilt cepat ke Jam Mekanik Raksasa yang berputar kencang → turun tajam ke pintu lift terbuka lebar!",
        visual_beat="Jam Raksasa & roda gigi berputar super cepat; dial lantai meluncur ke lantai 1; pintu lift kuningan bergeser terbuka dengan DING! Pak Bima (relieved -> proud) melompat girang!",
        sfx_cues=(
            SfxCue(0.12, "tick_fast", 0.90),
            SfxCue(0.56, "ding", 1.00),
            SfxCue(0.64, "door_slide", 0.85),
            SfxCue(0.84, "chime_aha", 0.75),
        ),
    ),
    SceneSpec(
        scene_id=10,
        slug="s10_outro_punchline",
        title="Outro & Micro-Gag: Ubah Cara Otak Merasakannya",
        default_duration_s=5.8,
        mood="golden_mirror",
        mirrors_on=True,
        rocket_on=True,
        narration="Kadang solusi terbaik bukan mengubah mesinnya—tapi mengubah cara otak kita merasakannya!",
        camera_note="Smooth heroic pull-back menyusuri karpet merah menuju wide shot lobi bercahaya sore emas.",
        visual_beat="Raka (smug -> laugh) mengangkat gelas kopi 3D ke kamera; Pak Doni masih asyik bercermin; micro-gag: Clara pelan-pelan menyeret kereta roket 3D-nya keluar frame dengan wajah kecewa datar!",
        sfx_cues=(
            SfxCue(0.10, "whoosh", 0.65),
            SfxCue(0.62, "sparkle", 0.75),
            SfxCue(0.82, "jazz_fin", 0.90),
        ),
    ),
]
