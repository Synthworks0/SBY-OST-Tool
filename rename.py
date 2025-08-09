import multiprocessing
import os
import re
import shutil
import sys
import json
import time
import tempfile

# Configure critical Qt environment BEFORE importing PySide6 or any module that imports PySide6
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ.setdefault("QT_DEBUG_PLUGINS", "1")

def _get_runtime_root_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _get_app_resources_dir() -> str:
    runtime_root = _get_runtime_root_dir()
    if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
        mac_resources = os.path.abspath(os.path.join(runtime_root, '..', 'Resources'))
        return mac_resources if os.path.isdir(mac_resources) else runtime_root
    return runtime_root

def _configure_qt_env_early() -> None:
    if "QT_MEDIA_BACKEND" not in os.environ:
        os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
    os.environ.setdefault("QT_MULTIMEDIA_PREFERRED_PLUGINS", "ffmpeg")

    # On macOS force Cocoa and set plugin/qml roots ahead of time
    runtime_root = _get_runtime_root_dir()
    resources_dir = _get_app_resources_dir()
    if sys.platform == 'darwin':
        os.environ.setdefault('QT_QPA_PLATFORM', 'cocoa')

    plugin_roots = [
        os.path.join(runtime_root, 'PySide6', 'Qt', 'plugins'),
        os.path.join(resources_dir, 'PySide6', 'Qt', 'plugins'),
        os.path.join(runtime_root, 'Qt', 'plugins'),
        os.path.join(resources_dir, 'Qt', 'plugins'),
    ]
    qml_roots = [
        os.path.join(runtime_root, 'PySide6', 'Qt', 'qml'),
        os.path.join(resources_dir, 'PySide6', 'Qt', 'qml'),
    ]

    existing_plugin_path = os.environ.get('QT_PLUGIN_PATH', '')
    merged_plugin_path = os.pathsep.join([
        *(p for p in plugin_roots if os.path.isdir(p)),
        *(existing_plugin_path.split(os.pathsep) if existing_plugin_path else []),
    ])
    if merged_plugin_path:
        os.environ['QT_PLUGIN_PATH'] = merged_plugin_path

    for root in plugin_roots:
        platforms_dir = os.path.join(root, 'platforms')
        if os.path.isdir(platforms_dir):
            os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', platforms_dir)
            break

    existing_qml_path = os.environ.get('QML2_IMPORT_PATH', '')
    merged_qml_path = os.pathsep.join([
        *(p for p in qml_roots if os.path.isdir(p)),
        *(existing_qml_path.split(os.pathsep) if existing_qml_path else []),
    ])
    if merged_qml_path:
        os.environ['QML2_IMPORT_PATH'] = merged_qml_path

# Apply early Qt env before any PySide6 import
_configure_qt_env_early()

import resources_rc
from mutagen.flac import FLAC
from PySide6.QtCore import QObject, Slot, Property, Signal, QUrl, QDir, QTimer, QThread, QLibraryInfo, QResource
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QFileSystemModel
from PySide6.QtGui import QIcon
from debug_logger import DebugLogger

DEBUG_MODE = True
debug_logger = DebugLogger(DEBUG_MODE)

albums = {
    "Bunny Girl Senpai": {
        "Japanese": "青春ブタ野郎はバニーガール先輩の夢を見ない Original Soundtrack",
        "Romaji": "Seishun Buta Yarou wa Bunny Girl Senpai no Yume wo Minai Original Soundtrack",
        "English": "Rascal Does Not Dream of Bunny Girl Senpai Original Soundtrack",
        "Tracks": {
            "Japanese": [
                "青春ブタ野郎", "麻衣さん", "カップル", "水平線", "大事なこと", "変態", "江の島", "ホショウ", "異分子", "都市伝説",
                "傷", "助けてくれ", "大真面目", "薄気味悪い空間", "ひとり", "東浜海水浴場", "バカ咲太!", "こうして、世界は桜島麻衣を取り戻した", "朝です…", "忍者ごっこ",
                "双葉", "乙女ちっく", "嫌悪感", "打ち上げ花火", "受話器の向こう", "2回目", "ピンクのビキニ", "乙女心", "入れ替わった姉妹", "わだかまり",
                "初恋の人"
            ],
            "Romaji": [
                "Seishun Buta Yarou", "Mai-san", "Kappuru", "Suiheisen", "Daiji na Koto", "Hentai", "Enoshima", "Hoshou", "Ibunshi", "Toshi Densetsu",
                "Kizu", "Tasukete Kure", "Oomajime", "Usukimiwarui Kuukan", "Hitori", "Higashihama Kaisuiyokujou", "Baka Sakuta!", "Koushite, Sekai wa Sakurajima Mai wo Torimodoshita", "Asa desu...", "Ninjagokko",
                "Futaba", "Otomechikku", "Ken'okan", "Uchiage Hanabi", "Juwaki no Mukou", "2 Kaime", "Pink no Bikini", "Otomegokoro", "Irekawatta Shimai", "Wadakamari",
                "Hatsukoi no Hito"
            ],
            "English": [
                "Rascal", "Mai-san", "Couple", "Horizon", "Something Precious", "Pervert", "Enoshima", "Guarantee", "Outsider", "Urban Legend",
                "Scar", "Help Me", "Deadly Serious", "An Eerie Room", "Alone", "Higashihama Beach", "Idiot Sakuta!", "And so, The World Regained Mai Sakurajima", "It's Morning...", "Playing Ninja",
                "Futaba", "Girlish", "Disgust", "Fireworks", "The Other End of the Receiver", "Second Time", "Pink Bikini", "A Girl's Feelings", "Swapped Sisters", "Reserve",
                "A First Love" # Translations all retrieved from `https://vgmdb.net/album/80667`
            ]
        }
    },
    "Dreaming Girl": {
        "Japanese": "青春ブタ野郎はゆめみる少女の夢を見ない Original Soundtrack",
        "Romaji": "Seishun Buta Yarou wa Yumemiru Shoujo no Yume wo Minai Original Soundtrack",
        "English": "Rascal Does Not Dream of a Dreaming Girl Original Soundtrack",
        "Tracks": {
            "Japanese": [
                "青春ブタ野郎はゆめみる少女の夢を見ない", "『ありがとう』と『頑張ったね』と『大好き』", "夢の姿", "書きたいこと", "昨日のこれ", "夢の中", "デート ～夢の世界～", "スローモーション", "決意の光",
                "真っ直ぐな想い", "辛い選択", "意外な言葉", "運命を分ける時間", "悲しみ", "選んだ道", "不安の果実", "馬鹿なこと", "この約束を守るために", "「ただいま」「おかえりなさい」",
                "生きることを選んだから", "小さな可能性のために", "もう一度", "満ち足りた顔", "静かな空気", "「さすが、梓川はブタ野郎だね」", "大切な名前"
            ],
            "Romaji": [
                "Seishun Buta Yarou wa Yumemiru Shoujo no Yume wo Minai", "'Arigato' to 'Ganbatte' to 'Daisuki'", "Yume no Sugata", "Kakitai Koto", "Kinou no Kore", "Yume no Naka", "Deeto ~Yume no Sekai~", "Slow Motion", "Ketsui no Hikari",
                "Massugu no Omoi", "Tsurai Sentaku", "Igai na Kotoba", "Unmei wo Wakeru Jikan", "Kanashimi", "Eranda Michi", "Fuan no Kajitsu", "Baka na Koto", "Kono Yakusoku wo Mamoru Tame ni", "'Tadaima' 'Okaerinasai'",
                "Ikiru Koto wo Eranda Kara", "Chiisana Kanousei no Tame ni", "Mouichidou", "Michitarita Kao", "Shizuka na Kuuki", "'Sasuga, Azusagawa wa Buta Yarou da ne'", "Taisetsu na Namae"
            ],
            "English": [
                "Rascal Does Not Dream of a Dreaming Girl", "'Thank You', 'You Did Well', and 'I Love You'", "Dream Figure", "What I Want to Write", "This Thing from Yesterday", "In A Dream", "Date ~Dream World~", "Slow Motion", "Light of Determination",
                "Straightforward Feelings", "A Painful Choice", "Unexpected Words", "The Moment That Divides Fate", "Sadness", "The Road of Choice", "The Fruit of Anxiety", "Foolish Thing", "To Keep This Promise", "'I'm home' 'Welcome back'",
                "Because I Chose to Live", "For a Small Possibility", "Once Again", "Satisfied Face", "Quiet Atmosphere", "'Nothing less from you, Azusagawa. Such a rascal'", "Important Name"
            ] # Translated from Youtube with adjusments made by me
        }
    },
    "Sister Venturing Out": {
        "Japanese": "青春ブタ野郎はおでかけシスターの夢を見ない Original Soundtrack",
        "Romaji": "Seishun Buta Yaro wa Odekake Sister no Yume wo Minai Original Soundtrack",
        "English": "Rascal Does Not Dream of a Sister Venturing Out Original Soundtrack",
        "Tracks": {
            "Japanese": [
                "奇妙な夢", "ノスタルジー", "やりきれない思い", "ひそかな悦び", "踊る気持ち", "花楓のお願い", "もしかして", "花楓のために", "うたたね", "ノックはした",
                "ご褒美-", "不安と緊張", "頑張れるから", "一歩ずつ", "心地のいい朝", "それでも心配", "舞い上がる咲太", "不安な知らせ", "止まらない怖さ", "かえでの夢",
                "戸惑い", "泣いた分と同じだけ嬉しかった", "花楓の成長", "自分で決めた道", "夢の続き"
            ],
            "Romaji": [
                "Kimyou na Yume", "Nostalgia", "Yarikirenai Omoi", "Hisokana Yorokobi", "Odoru Kimochi", "Kaede no Onegai", "Moshikashite", "Kaede no Tame ni", "Utatane", "Nokku wa Shita",
                "Gohoubi-", "Fuan to Kinchou", "Ganbareru kara", "Ippo Zutsu", "Kokochi no Ii Asa", "Soredemo Shinpai", "Maiagaru Sakuta", "Fuan na Shirase", "Tomaranai Kowasa", "Kaede no Yume",
                "Tomadoi", "Naita Bun to Onaji Dake Ureshikatta", "Kaede no Seichou", "Jibun de Kimeta Michi", "Yume no Tsuzuki"
            ],
            "English": [
                "A Strange Dream", "Nostalgia", "Unbearable Feelings", "Secret Joy", "Dancing Heart", "Kaede's Request", "Perhaps...", "For Kaede", "A Nap", "I Did Knock",
                "A Reward", "Anxiety and Tension", "Because I Can Keep Going", "Step by Step", "A Pleasant Morning", "Still Worried", "Excited Sakuta", "Troubling News", "An Unstoppable Fear", "Kaede's Dream",
                "Bewilderment", "My Happiness Matched My Tears", "Kaede's Growth", "The Path I Chose", "Continuation of the Dream"
            ] # Translated by me
        }
    },
    "Knapsack Kid": {
        "Japanese": "青春ブタ野郎はランドセルガールの夢を見ない Original Soundtrack",
        "Romaji": "Seishun Buta Yarou wa Randoseru Girl no Yume wo Minai Original Soundtrack",
        "English": "Rascal Does Not Dream of a Knapsack Kid Original Soundtrack",
        "Tracks": {
            "Japanese": [
                "同じ夢", "大事なもの", "お守り", "お約束", "花楓の願い", "考え事", "沈黙の雨", "再会", "幸せな時間",
                "咲太の思春期症候群", "一緒に帰る", "高まる不安", "違和感", "疑い", "咲太の決心", "どうしても", "もう少しの辛抱", "お守りと約束", "麻衣の優しさ",
                "安心", "頑張ったから", "家族", "見えない謎", "入学おめでとう"
            ],
            "Romaji": [
                "Onaji Yume", "Taisetsu na Mono", "Omamori", "Oyakusoku", "Hanafū no Negai", "Kangaegoto", "Chinmoku no Ame", "Saikai", "Shiawase na Jikan",
                "Sakuta no Shishunki Shoukougun", "Issho ni Kaeru", "Takamaru Fuan", "Iwakan", "Utagai", "Sakuta no Kesshin", "Doushitemo", "Mou Sukoshi no Shinbou", "Omamori to Yakusoku", "Mai no Yasashisa",
                "Anshin", "Ganbatta kara", "Kazoku", "Mienai Nazo", "Nyuugaku Omedetou"
            ],
            "English": [
                "The Same Dream", "Something Important", "Amulet", "Promise", "Kaede's Wish", "Contemplation", "Silent Rain", "Reunion", "Happy Times",
                "Sakuta's Adolescence Syndrome", "Walking Home Together", "Growing Anxiety", "Sense of Discomfort", "Doubt", "Sakuta's Determination", "No Matter What", "Just a Little More Patience", "Amulet and a Promise", "Mai's Kindness",
                "Relief", "Because I Gave It My All", "Family", "Invisible Mystery", "Congratulations on Your Enrollment"
            ] # Translated by me
        }
    },
    "Extras": {
        "Japanese": "エクストラ",
        "Romaji": "Ekusutora",
        "English": "Extras",
        "Tracks": [
            {
                "subfolder": {
                    "Japanese": "不可思議のカルテ",
                    "Romaji": "Fukashigi no Karte",
                    "English": "Fukashigi no Karte"
                },
                "filename": "Fukashigi no Karte.flac",
                "titles": {
                    "Japanese": "不可思議のカルテ",
                    "Romaji": "Fukashigi no Karte",
                    "English": "Fukashigi no Karte"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ",
                    "Romaji": "Fukashigi no Karte",
                    "English": "Fukashigi no Karte"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "桜島麻衣(CV:瀬戸麻沙美), 古賀朋絵(CV:東山奈央), 双葉理央(CV:種﨑敦美), 豊浜のどか(CV:内田真礼), 梓川かえで(CV:久保ユリカ), 牧之原翔子(CV:水瀬いのり)",
                    "Romaji": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)",
                    "English": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "不可思議のカルテ 全ヒロインVer.",
                    "Romaji": "Fukashigi no Karte All Heroine Ver.",
                    "English": "Fukashigi no Karte (All Heroine Ver.)"
                },
                "filename": "Fukashigi no Karte (All Heroine Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (全ヒロインVer.)",
                    "Romaji": "Fukashigi no Karte (All Heroine Ver.)",
                    "English": "Fukashigi no Karte (All Heroine Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ 全ヒロインVer.",
                    "Romaji": "Fukashigi no Karte All Heroine Ver.",
                    "English": "Fukashigi no Karte All Heroine Ver."
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "桜島麻衣(CV:瀬戸麻沙美), 古賀朋絵(CV:東山奈央), 双葉理央(CV:種﨑敦美), 豊浜のどか(CV:内田真礼), 梓川かえで(CV:久保ユリカ), 牧之原翔子(CV:水瀬いのり)",
                    "Romaji": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)",
                    "English": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "不可思議のカルテ インストゥルメンタルVer.",
                    "Romaji": "Fukashigi no Karte Instrumental Ver.",
                    "English": "Fukashigi no Karte (Instrumental Ver.)"
                },
                "filename": "Fukashigi no Karte (Instrumental Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (インストゥルメンタルVer.)",
                    "Romaji": "Fukashigi no Karte (Instrumental Ver.)",
                    "English": "Fukashigi no Karte (Instrumental Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ インストゥルメンタルVer.",
                    "Romaji": "Fukashigi no Karte Instrumental Ver.",
                    "English": "Fukashigi no Karte Instrumental Ver."
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "fox capture plan",
                    "Romaji": "fox capture plan",
                    "English": "fox capture plan"
                },
                "album_artists": {
                    "Japanese": "fox capture plan",
                    "Romaji": "fox capture plan",
                    "English": "fox capture plan"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "不可思議のカルテ ジュブナイルVer.",
                    "Romaji": "Fukashigi no Karte Juvenile Ver.",
                    "English": "Fukashigi no Karte (Juvenile Ver.)"
                },
                "filename": "Fukashigi no Karte (Juvenile Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (ジュブナイルVer.)",
                    "Romaji": "Fukashigi no Karte (Juvenile Ver.)",
                    "English": "Fukashigi no Karte (Juvenile Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ ジュブナイルVer.",
                    "Romaji": "Fukashigi no Karte Juvenile Ver.",
                    "English": "Fukashigi no Karte Juvenile Ver."
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "桜島麻衣(CV:瀬戸麻沙美), 古賀朋絵(CV:東山奈央), 双葉理央(CV:種﨑敦美), 豊浜のどか(CV:内田真礼), 梓川かえで(CV:久保ユリカ), 牧之原翔子(CV:水瀬いのり)",
                    "Romaji": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)",
                    "English": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "不可思議のカルテ 映画Ver.",
                    "Romaji": "Fukashigi no Karte Movie Ver.",
                    "English": "Fukashigi no Karte (Movie Ver.)"
                },
                "filename": "Fukashigi no Karte (Movie Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (映画Ver.)",
                    "Romaji": "Fukashigi no Karte (Movie Ver.)",
                    "English": "Fukashigi no Karte (Movie Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ 映画Ver.",
                    "Romaji": "Fukashigi no Karte Movie Ver.",
                    "English": "Fukashigi no Karte Movie Ver."
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "桜島麻衣(CV:瀬戸麻沙美), 古賀朋絵(CV:東山奈央), 双葉理央(CV:種﨑敦美), 豊浜のどか(CV:内田真礼), 梓川かえで(CV:久保ユリカ), 牧之原翔子(CV:水瀬いのり)",
                    "Romaji": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)",
                    "English": "Mai Sakurajima(CV:Asami Seto), Tomoe Koga(CV:Nao Toyama), Rio Futaba(CV:Atsumi Tanezaki), Nodoka Toyohama(CV:Maaya Uchida), Kaede Azusagawa(CV:Yurika Kubo), Shoko Makinohara(CV:Inori Minase)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "花楓&かえで",
                    "Romaji": "Kaede and Kaede",
                    "English": "Kaede and Kaede"
                },
                "filename": "Fukashigi no Karte (Kaede and Kaede Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (花楓&かえでVer.)",
                    "Romaji": "Fukashigi no Karte (Kaede and Kaede Ver.)",
                    "English": "Fukashigi no Karte (Kaede & Kaede Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (花楓&かえでVer.)",
                    "Romaji": "Fukashigi no Karte (Kaede and Kaede Ver.)",
                    "English": "Fukashigi no Karte (Kaede & Kaede Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "梓川花楓&かえで(CV:久保ユリカ)",
                    "Romaji": "Kaede Azusagawa & Kaede(CV:Yurika Kubo)",
                    "English": "Kaede Azusagawa & Kaede (CV: Yurika Kubo)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "梓川 花楓",
                    "Romaji": "Azusagawa Kaede",
                    "English": "Kaede Azusagawa"
                },
                "filename": "Fukashigi no Karte (Kaede Azusagawa Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (梓川花楓Ver.)",
                    "Romaji": "Fukashigi no Karte (Azusagawa Kaede Ver.)",
                    "English": "Fukashigi no Karte (Kaede Azusagawa Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (梓川花楓Ver.)",
                    "Romaji": "Fukashigi no Karte (Azusagawa Kaede Ver.)",
                    "English": "Fukashigi no Karte (Kaede Azusagawa Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "梓川花楓(CV:久保ユリカ)",
                    "Romaji": "Kaede Azusagawa(CV:Yurika Kubo)",
                    "English": "Kaede Azusagawa(CV:Yurika Kubo)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "桜島 麻衣",
                    "Romaji": "Sakurajima Mai",
                    "English": "Mai Sakurajima"
                },
                "filename": "Fukashigi no Karte (Mai Sakurajima Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (桜島麻衣Ver.)",
                    "Romaji": "Fukashigi no Karte (Sakurajima Mai Ver.)",
                    "English": "Fukashigi no Karte (Mai Sakurajima Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (桜島麻衣Ver.)",
                    "Romaji": "Fukashigi no Karte (Sakurajima Mai Ver.)",
                    "English": "Fukashigi no Karte (Mai Sakurajima Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "桜島麻衣(CV:瀬戸麻沙美)",
                    "Romaji": "Mai Sakurajima(CV:Asami Seto)",
                    "English": "Mai Sakurajima(CV:Asami Seto)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "豊浜 のどか",
                    "Romaji": "Toyohama Nodoka",
                    "English": "Nodoka Toyohama"
                },
                "filename": "Fukashigi no Karte (Nodoka Toyohama Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (豊浜のどかVer.)",
                    "Romaji": "Fukashigi no Karte (Toyohama Nodoka Ver.)",
                    "English": "Fukashigi no Karte (Nodoka Toyohama Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (豊浜のどかVer.)",
                    "Romaji": "Fukashigi no Karte (Toyohama Nodoka Ver.)",
                    "English": "Fukashigi no Karte (Nodoka Toyohama Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "豊浜のどか(CV:内田真礼)",
                    "Romaji": "Nodoka Toyohama(CV:Maaya Uchida)",
                    "English": "Nodoka Toyohama(CV:Maaya Uchida)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "双葉 理央",
                    "Romaji": "Futaba Rio",
                    "English": "Rio Futaba"
                },
                "filename": "Fukashigi no Karte (Rio Futaba Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (双葉理央Ver.)",
                    "Romaji": "Fukashigi no Karte (Futaba Rio Ver.)",
                    "English": "Fukashigi no Karte (Rio Futaba Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (双葉理央Ver.)",
                    "Romaji": "Fukashigi no Karte (Futaba Rio Ver.)",
                    "English": "Fukashigi no Karte (Rio Futaba Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "双葉理央(CV:種﨑敦美)",
                    "Romaji": "Rio Futaba(CV:Atsumi Tanezaki)",
                    "English": "Rio Futaba(CV:Atsumi Tanezaki)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "梓川 咲太",
                    "Romaji": "Azusagawa Sakuta",
                    "English": "Sakuta Azusagawa"
                },
                "filename": "Fukashigi no Karte (Azusagawa Sakuta Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (梓川咲太Ver.)",
                    "Romaji": "Fukashigi no Karte (Azusagawa Sakuta Ver.)",
                    "English": "Fukashigi no Karte (Sakuta Azusagawa Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (梓川咲太Ver.)",
                    "Romaji": "Fukashigi no Karte (Azusagawa Sakuta Ver.)",
                    "English": "Fukashigi no Karte (Sakuta Azusagawa Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "梓川咲太(CV:石川界人)",
                    "Romaji": "Sakuta Azusagawa(CV:Kaito Ishikawa)",
                    "English": "Sakuta Azusagawa(CV:Kaito Ishikawa)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "牧之原 翔子",
                    "Romaji": "Makinohara Shoko",
                    "English": "Shoko Makinohara"
                },
                "filename": "Fukashigi no Karte (Shoko Makinohara Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (牧之原翔子Ver.)",
                    "Romaji": "Fukashigi no Karte (Makinohara Shoko Ver.)",
                    "English": "Fukashigi no Karte (Shoko Makinohara Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (牧之原翔子Ver.)",
                    "Romaji": "Fukashigi no Karte (Makinohara Shoko Ver.)",
                    "English": "Fukashigi no Karte (Shoko Makinohara Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "牧之原翔子(CV:水瀬いのり)",
                    "Romaji": "Shoko Makinohara(CV:Inori Minase)",
                    "English": "Shoko Makinohara(CV:Inori Minase)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "古賀 朋絵",
                    "Romaji": "Tomoe Koga",
                    "English": "Tomoe Koga"
                },
                "filename": "Fukashigi no Karte (Tomoe Koga Ver.).flac",
                "titles": {
                    "Japanese": "不可思議のカルテ (古賀朋絵Ver.)",
                    "Romaji": "Fukashigi no Karte (Tomoe Koga Ver.)",
                    "English": "Fukashigi no Karte (Tomoe Koga Ver.)"
                },
                "album_title": {
                    "Japanese": "不可思議のカルテ (古賀朋絵Ver.)",
                    "Romaji": "Fukashigi no Karte (Tomoe Koga Ver.)",
                    "English": "Fukashigi no Karte (Tomoe Koga Ver.)"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "古賀朋絵(CV:東山奈央)",
                    "Romaji": "Tomoe Koga(CV:Nao Toyama)",
                    "English": "Tomoe Koga(CV:Nao Toyama)"
                },
                "album_artists": {
                    "Japanese": "fox capture plan; Various Artists",
                    "Romaji": "fox capture plan; Various Artists",
                    "English": "fox capture plan; Various Artists"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "Sweet Bullet/BABY!",
                    "Romaji": "Sweet Bullet/BABY!",
                    "English": "Sweet Bullet/BABY!"
                },
                "filename": "BABY!.flac",
                "titles": {
                    "Japanese": "BABY!",
                    "Romaji": "BABY!",
                    "English": "BABY!"
                },
                "album_title": {
                    "Japanese": "BABY!",
                    "Romaji": "BABY!",
                    "English": "BABY!"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "album_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "Sweet Bullet/BABY!",
                    "Romaji": "Sweet Bullet/BABY!",
                    "English": "Sweet Bullet/BABY!"
                },
                "filename": "BABY! (Instrumental Ver.).flac",
                "titles": {
                    "Japanese": "BABY! (インストゥルメンタルVer.)",
                    "Romaji": "BABY! (Instrumental Ver.)",
                    "English": "BABY! (Instrumental Ver.)"
                },
                "album_title": {
                    "Japanese": "BABY!",
                    "Romaji": "BABY!",
                    "English": "BABY!"
                },
                "track_number": 2,
                "contributing_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "album_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "Sweet Bullet/ミューズになっちゃう",
                    "Romaji": "Sweet Bullet/Museninaccyau",
                    "English": "Sweet Bullet/Becoming a Muse"
                },
                "filename": "Becoming a Muse.flac",
                "titles": {
                    "Japanese": "ミューズになっちゃう",
                    "Romaji": "Museninaccyau",
                    "English": "Becoming a Muse"
                },
                "album_title": {
                    "Japanese": "ミューズになっちゃう",
                    "Romaji": "Museninaccyau",
                    "English": "Becoming a Muse"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "album_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "Sweet Bullet/ミューズになっちゃう",
                    "Romaji": "Sweet Bullet/Museninaccyau",
                    "English": "Sweet Bullet/Becoming a Muse"
                },
                "filename": "Becoming a Muse (Instrumental Ver.).flac",
                "titles": {
                    "Japanese": "ミューズになっちゃう (インストゥルメンタルVer.)",
                    "Romaji": "Museninaccyau (Instrumental Ver.)",
                    "English": "Becoming a Muse (Instrumental Ver.)"
                },
                "album_title": {
                    "Japanese": "ミューズになっちゃう",
                    "Romaji": "Museninaccyau",
                    "English": "Becoming a Muse"
                },
                "track_number": 2,
                "contributing_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "album_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "Sweet Bullet/オトメノート",
                    "Romaji": "Sweet Bullet/Otomenote",
                    "English": "Sweet Bullet/Otome Notebook"
                },
                "filename": "Otome Notebook.flac",
                "titles": {
                    "Japanese": "オトメノート", 
                    "Romaji": "Otomenote",
                    "English": "Otome Notebook" # `オトメ` wasn't translated here
                },
                "album_title": {
                    "Japanese": "オトメノート",
                    "Romaji": "Otomenote",
                    "English": "Otome Notebook"
                },
                "track_number": 1,
                "contributing_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "album_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "genre": "Film; Anime"
            },
            {
                "subfolder": {
                    "Japanese": "Sweet Bullet/オトメノート",
                    "Romaji": "Sweet Bullet/Otomenote",
                    "English": "Sweet Bullet/Otome Notebook"
                },
                "filename": "Otome Notebook (Instrumental Ver.).flac",
                "titles": {
                    "Japanese": "オトメノート (インストゥルメンタルVer.)",
                    "Romaji": "Otomenote (Instrumental Ver.)",
                    "English": "Otome Notebook (Instrumental Ver.)"
                },
                "album_title": {
                    "Japanese": "オトメノート",
                    "Romaji": "Otomenote",
                    "English": "Otome Notebook"
                },
                "track_number": 2,
                "contributing_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "album_artists": {
                    "Japanese": "Sweet Bullet",
                    "Romaji": "Sweet Bullet",
                    "English": "Sweet Bullet"
                },
                "genre": "Film; Anime"
            }
        ]
    }
}

class Renamer:
    def __init__(self):
        resources_dir = _get_app_resources_dir()
        # Root where the app's data assets are stored (contains the 'resources' folder)
        self._resources_root = os.path.join(resources_dir, "resources")
        self.base_dir = os.path.join(self._resources_root, "SBY Soundtracks")
        self.albums = albums
        self.qml_path = os.path.join(resources_dir, "main.qml")

    def rename_files(self, album_name, language):
        try:
            album_dir = os.path.join(self.base_dir, self.albums[album_name]["English"])
            if not os.path.exists(album_dir) or len(os.listdir(album_dir)) == 0:
                return f"Error: No files found for {self.albums[album_name][language]}"

            track_names = self.albums[album_name]["Tracks"][language]
            files_renamed = 0

            for i, new_name in enumerate(track_names, 1):
                for file in os.listdir(album_dir):
                    if file.endswith(".flac"):
                        audio = FLAC(os.path.join(album_dir, file))
                        if int(audio["tracknumber"][0]) == i:
                            old_path = os.path.join(album_dir, file)
                            new_path = os.path.join(album_dir, f"{i:02d}. {new_name}.flac")
                            os.rename(old_path, new_path)
                            
                            audio = FLAC(new_path)
                            audio["title"] = new_name
                            audio["album"] = self.albums[album_name][language]
                            audio.save()
                            files_renamed += 1
                            break

            if files_renamed == 0:
                return f"Error: No matching files found for {self.albums[album_name][language]}"
            return f"Files renamed successfully for {self.albums[album_name][language]}"
        except Exception as e:
            return f"Error: Failed to rename files. {str(e)}"

class RenamerBackend(QObject, Renamer):
    albumsChanged = Signal()
    coverImageChanged = Signal()
    outputFolderChanged = Signal()
    folderContentsChanged = Signal()
    driveListChanged = Signal()
    extractionFinished = Signal(str)
    albumStateChanged = Signal()
    currentAlbumChanged = Signal()
    currentLanguageChanged = Signal()
    canExtractChanged = Signal()
    songListChanged = Signal()
    currentPathChanged = Signal()

    def __init__(self):
        QObject.__init__(self)
        Renamer.__init__(self)
        # Ensure QML can resolve the resources prefix to our packaged resources folder
        try:
            QDir.addSearchPath("resources", self.get_resource_path())
        except Exception as e:
            debug_logger.error(f"Failed to add QML resources search path: {e}")
        self._current_album = list(self.albums.keys())[0]
        self._current_language = "English"
        self._output_folder = ""
        self._current_path = ""
        self._folder_contents = []
        self._drive_list = []
        self._album_states = {album: "extract" for album in self.albums}
        self._song_list = []
        self.load_last_output_folder()
        QTimer.singleShot(0, self.initialize_file_system)
        self._include_track_numbers = True

    def initialize_file_system(self):
        self._drive_list = [drive.absoluteFilePath() for drive in QDir.drives()]
        self.driveListChanged.emit()
        self.update_folder_contents()

    @Property(str, notify=outputFolderChanged)
    def output_folder(self):
        return self._output_folder
    
    @Property(str, notify=currentAlbumChanged)
    def current_album(self):
        return self._current_album

    def save_last_output_folder(self):
        config = {'last_output_folder': self._output_folder}
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f)
        except Exception as e:
            debug_logger.error(f"Error saving config: {str(e)}")

    def load_last_output_folder(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                last_folder = config.get('last_output_folder', '')
                self.set_output_folder(last_folder)
        except FileNotFoundError:
            pass
        except Exception as e:
            debug_logger.error(f"Error loading config: {str(e)}")

    @Slot(str)
    def set_output_folder(self, folder):
        if self._output_folder != folder:
            self._output_folder = folder
            self.outputFolderChanged.emit()
            self.save_last_output_folder()
            self.check_and_create_soundtracks()
            self.canExtractChanged.emit()
            self.update_song_list()

    @Property('QVariantList', notify=driveListChanged)
    def drive_list(self):
        return self._drive_list

    @Property('QVariantList', notify=folderContentsChanged)
    def folder_contents(self):
        return self._folder_contents
    
    @Property(bool, constant=True)
    def is_frozen(self):
        return getattr(sys, 'frozen', False)

    @Slot(str)
    def set_current_path(self, path):
        if self._current_path != path:
            self._current_path = path
            self.update_folder_contents()

    @Slot()
    def update_folder_contents(self):
        self._folder_contents.clear()
        
        if not self._current_path:
            self._folder_contents = [{"name": drive, "path": drive, "isDir": True} for drive in self._drive_list]
        else:
            dir = QDir(self._current_path)
            dir.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
            dir.setSorting(QDir.Name)
            
            for folder in dir.entryInfoList():
                self._folder_contents.append({
                    "name": folder.fileName(),
                    "path": folder.filePath(),
                    "isDir": folder.isDir()
                })
        
        self.folderContentsChanged.emit()

    @Slot(str, result=str)
    def get_parent_directory(self, path):
        dir = QDir(path)
        if dir.cdUp():
            return dir.absolutePath()
        return ""

    @Slot(str, str, result=bool)
    def create_new_folder(self, parent_path, folder_name):
        dir = QDir(parent_path)
        if dir.mkdir(folder_name):
            self.update_folder_contents()
            return True
        return False
    
    @Slot(str, str, result=str)
    def join_paths(self, path1, path2):
        return os.path.join(path1, path2)
    
    def check_and_create_soundtracks(self):
        sby_folder = os.path.join(self._output_folder, "SBY Soundtracks")
        os.makedirs(sby_folder, exist_ok=True)
        for album_name in self.albums:
            album_folder = os.path.join(sby_folder, self.albums[album_name]["English"])
            if os.path.exists(album_folder) and len(os.listdir(album_folder)) > 0:
                self._album_states[album_name] = "rename"
            else:
                self._album_states[album_name] = "extract"
        self.albumStateChanged.emit()

    def check_rename_soundtrack(self, album_name):
        album_folder = os.path.join(self._output_folder, "SBY Soundtracks", self.albums[album_name]["English"])
        if os.path.exists(album_folder) and len(os.listdir(album_folder)) > 0:
            self.extractionFinished.emit(f"Soundtrack '{album_name}' found. Ready to rename.")
        else:
            self.extractionFinished.emit(f"Soundtrack '{album_name}' not found.")

    @Slot(str)
    def extract_soundtrack(self, album_name):
        source_dir = self.get_resource_path("SBY Soundtracks", self.albums[album_name]["English"])
        destination_dir = os.path.join(self._output_folder, "SBY Soundtracks", self.albums[album_name][self._current_language])

        if not os.path.exists(source_dir):
            self.extractionFinished.emit(f"Error: Soundtrack '{album_name}' not found")
            return

        try:
            os.makedirs(destination_dir, exist_ok=True)

            if album_name == "Extras":
                self.extract_and_rename_extras(source_dir, destination_dir)
            else:
                cover_source = os.path.join(source_dir, "cover.jpg")
                if os.path.exists(cover_source):
                    cover_dest = os.path.join(destination_dir, "cover.jpg")
                    shutil.copy2(cover_source, cover_dest)

                files = sorted([f for f in os.listdir(source_dir) if f.endswith(".flac")])
                for i, file in enumerate(files, 1):
                    source_file = os.path.join(source_dir, file)
                    
                    base_name = re.sub(r'^\d+\.\s*', '', os.path.splitext(file)[0])
                    
                    if self._include_track_numbers:
                        new_filename = f"{i:02d}. {base_name}.flac"
                    else:
                        new_filename = f"{base_name}.flac"
                    
                    dest_file = os.path.join(destination_dir, new_filename)
                    shutil.copy2(source_file, dest_file)

            self._album_states[album_name] = "rename"
            self.albumStateChanged.emit()
            self.extractionFinished.emit(f"Soundtrack '{album_name}' extracted successfully")

            self.set_current_album(album_name)
            self.rename_files()
        except Exception as e:
            self.extractionFinished.emit(f"Error extracting soundtrack: {str(e)}")

    def extract_and_rename_extras(self, source_dir, destination_dir):
        for track in self.albums["Extras"]["Tracks"]:
            subfolder = track.get("subfolder", {})
            filename = track.get("filename", "")
            
            source_subfolder = None
            if subfolder:
                source_subfolder_name = subfolder.get("English", "")
                if source_subfolder_name:
                    source_subfolder = os.path.join(source_dir, *source_subfolder_name.split('/'))
            
            dest_subfolder = None
            if subfolder:
                dest_subfolder_name = subfolder.get(self._current_language, "")
                if dest_subfolder_name:
                    dest_subfolder = os.path.join(destination_dir, *dest_subfolder_name.split('/'))
            
            if not source_subfolder or not os.path.exists(source_subfolder):
                debug_logger.error(f"Source subfolder not found: {source_subfolder}")
                continue
                
            if not dest_subfolder:
                dest_subfolder = destination_dir
                
            os.makedirs(dest_subfolder, exist_ok=True)
            
            source_file = os.path.join(source_subfolder, filename)
            if os.path.exists(source_file):
                dest_file = os.path.join(dest_subfolder, filename)
                shutil.copy2(source_file, dest_file)
                
                cover_source = os.path.join(source_subfolder, "cover.jpg")
                if os.path.exists(cover_source):
                    cover_dest = os.path.join(dest_subfolder, "cover.jpg")
                    shutil.copy2(cover_source, cover_dest)
                    
                if filename.endswith('.flac'):
                    audio = FLAC(dest_file)
                    audio["title"] = track["titles"][self._current_language]
                    audio["album"] = track["album_title"][self._current_language]
                    audio["tracknumber"] = str(track["track_number"])
                    audio["artist"] = track["contributing_artists"][self._current_language]
                    audio["albumartist"] = track["album_artists"][self._current_language]
                    audio["genre"] = track["genre"]
                    audio.save()

    @Slot(result=bool)
    def can_extract(self):
        return bool(self._output_folder)

    @Slot(result=str)
    def get_current_album_state(self):
        return self._album_states.get(self._current_album, "extract")

    def get_resource_path(self, *paths):
        # Point to the packaged 'resources' directory cross-platform
        try:
            resources_dir = self._resources_root
        except AttributeError:
            # Fallback for safety if base init didn't run as expected
            resources_dir = os.path.join(_get_app_resources_dir(), "resources")
        return os.path.join(resources_dir, *paths)


    @Slot(result=bool)
    def check_files_exist(self):
        if not self._output_folder:
            return False
        album_dir = os.path.join(self._output_folder, "SBY Soundtracks", self.albums[self._current_album]["English"])
        return os.path.exists(album_dir) and len(os.listdir(album_dir)) > 0

    @Slot(result=str)
    def get_album_path(self):
        return os.path.join(self._output_folder, "SBY Soundtracks", self.albums[self._current_album]["English"])

    @Slot(str)
    def extraction_finished(self, result):
        self.extractionFinished.emit(result)

    @Property(list, notify=albumsChanged)
    def album_list(self):
        return list(self.albums.keys())

    @Property(str, notify=coverImageChanged)
    def cover_image(self):
        cover_path = os.path.join(self.base_dir, self.albums[self._current_album]["English"], "cover.jpg")
        return QUrl.fromLocalFile(cover_path).toString() if os.path.exists(cover_path) else ""
    
    @current_album.setter
    def current_album(self, album):
        if self._current_album != album:
            self._current_album = album
            self.currentAlbumChanged.emit()
            self.coverImageChanged.emit()
            self.albumStateChanged.emit()
            self.update_song_list()

    @Slot(str)
    def set_current_album(self, album):
        self.current_album = album
    
    @Property(str, notify=currentLanguageChanged)
    def current_language(self):
        return self._current_language
    
    @current_language.setter
    def current_language(self, language):
        if self._current_language != language:
            self._current_language = language
            self.currentLanguageChanged.emit()
            self.update_song_list()

    @Slot(str)
    def set_current_language(self, language):
        self.current_language = language

    @Property(list, notify=songListChanged)
    def songList(self):
        return self._song_list

    def update_song_list(self):
        self._song_list.clear()

        album_dir = self.get_resource_path("SBY Soundtracks", self.albums[self._current_album]["English"])

        if os.path.exists(album_dir):
            if self._current_album != "Extras":
                track_titles = self.albums[self._current_album]["Tracks"][self._current_language]
                flac_files = sorted([f for f in os.listdir(album_dir) if f.endswith(".flac")])

                for i, file in enumerate(flac_files):
                    file_path = os.path.join(album_dir, file)
                    audio = FLAC(file_path)
                    duration = int(audio.info.length)
                    minutes = duration // 60
                    seconds = duration % 60
                    length_str = f"{minutes}:{seconds:02d}"

                    if i < len(track_titles):
                        title = track_titles[i]
                    else:
                        title = os.path.splitext(file)[0]

                    file_url = QUrl.fromLocalFile(file_path).toString()
                    self._song_list.append({
                        "title": title,
                        "length": length_str,
                        "filePath": file_url
                    })
            else:
                self.update_extras_song_list(album_dir)
        else:
            debug_logger.error(f"Album path does not exist: {album_dir}")
        self.songListChanged.emit()

    def update_extras_song_list(self, album_dir):
        track_list = self.albums["Extras"]["Tracks"]
        for track in track_list:
            subfolder = track.get("subfolder", {})
            filename = track.get("filename", "")
            titles = track.get("titles", {})
            title = titles.get(self._current_language, "")
            file_path = ""

            if subfolder:
                subfolder_name = subfolder.get("English", "")
                subfolder_path = os.path.join(album_dir, subfolder_name)
                if filename:
                    file_path = os.path.join(subfolder_path, filename)
                else:
                    flac_files = [f for f in os.listdir(subfolder_path) if f.endswith(".flac")]
                    if flac_files:
                        file_path = os.path.join(subfolder_path, flac_files[0])
            else:
                if filename:
                    file_path = os.path.join(album_dir, filename)
                else:
                    flac_files = [f for f in os.listdir(album_dir) if f.endswith(".flac")]
                    if flac_files:
                        file_path = os.path.join(album_dir, flac_files[0])

            if os.path.exists(file_path):
                audio = FLAC(file_path)
                duration = int(audio.info.length)
                minutes = duration // 60
                seconds = duration % 60
                length_str = f"{minutes}:{seconds:02d}"

                file_url = QUrl.fromLocalFile(file_path).toString()
                self._song_list.append({
                    "title": title if title else os.path.splitext(os.path.basename(file_path))[0],
                    "length": length_str,
                    "filePath": file_url
                })

    @Slot(result=str)
    def rename_files(self):
        try:
            album_parent_dir = os.path.join(self._output_folder, "SBY Soundtracks")
            album_dir = os.path.join(album_parent_dir, self.albums[self._current_album][self._current_language])

            if not os.path.exists(album_dir):
                found = False
                for lang in ["English", "Romaji", "Japanese"]:
                    possible_dir = os.path.join(album_parent_dir, self.albums[self._current_album][lang])
                    if os.path.exists(possible_dir):
                        os.rename(possible_dir, album_dir)
                        found = True
                        break
                if not found:
                    return f"Error: No files found for {self.albums[self._current_album][self._current_language]}"

            if self._current_album == "Extras":
                return self.rename_extras_files(album_dir)
            else:
                return self.rename_regular_files(album_dir)
        except Exception as e:
            return f"Error renaming files: {str(e)}"

    def rename_regular_files(self, album_dir):
        track_names = self.albums[self._current_album]["Tracks"][self._current_language]
        files_renamed = 0

        album_parent_dir = os.path.dirname(album_dir)
        new_album_dir = os.path.join(album_parent_dir, self.albums[self._current_album][self._current_language])

        if album_dir != new_album_dir:
            os.rename(album_dir, new_album_dir)
            album_dir = new_album_dir

        for i, new_name in enumerate(track_names, 1):
            for file in os.listdir(album_dir):
                if file.endswith(".flac"):
                    old_path = os.path.join(album_dir, file)
                    audio = FLAC(old_path)
                    if int(audio["tracknumber"][0]) == i:
                        if self._include_track_numbers:
                            new_filename = f"{i:02d}. {new_name}.flac"
                        else:
                            new_filename = f"{new_name}.flac"
                        new_path = os.path.join(album_dir, new_filename)
                        os.rename(old_path, new_path)

                        audio = FLAC(new_path)
                        audio["title"] = new_name
                        audio["album"] = self.albums[self._current_album][self._current_language]
                        audio["tracknumber"] = str(i)
                        audio.save()
                        files_renamed += 1
                        break

        if files_renamed == 0:
            return f"Error: No matching files found for {self.albums[self._current_album][self._current_language]}"
        self.coverImageChanged.emit()
        return f"Files renamed successfully for {self.albums[self._current_album][self._current_language]}"

    def rename_extras_files(self, extras_dir):
        track_list = self.albums["Extras"]["Tracks"]
        files_renamed = 0

        album_parent_dir = os.path.dirname(extras_dir)
        new_extras_dir = os.path.join(album_parent_dir, self.albums["Extras"][self._current_language])

        if extras_dir != new_extras_dir:
            if os.path.exists(new_extras_dir):
                shutil.rmtree(new_extras_dir)
            os.rename(extras_dir, new_extras_dir)
            extras_dir = new_extras_dir

        subfolder_renames = {}
        for track in track_list:
            subfolder = track.get("subfolder", {})
            subfolder_name_current_lang = subfolder.get(self._current_language, "")
            if subfolder_name_current_lang:
                current_subfolder_path = None
                for lang in ["Japanese", "Romaji", "English"]:
                    possible_subfolder_name = subfolder.get(lang, "")
                    if possible_subfolder_name:
                        possible_subfolder_parts = possible_subfolder_name.split('/')
                        possible_subfolder_path = os.path.join(extras_dir, *possible_subfolder_parts)
                        if os.path.exists(possible_subfolder_path):
                            current_subfolder_path = possible_subfolder_path
                            break

                if current_subfolder_path:
                    desired_subfolder_parts = subfolder_name_current_lang.split('/')
                    desired_subfolder_path = os.path.join(extras_dir, *desired_subfolder_parts)
                    if current_subfolder_path != desired_subfolder_path:
                        subfolder_renames[current_subfolder_path] = desired_subfolder_path

        subfolder_renames_sorted = sorted(subfolder_renames.items(), key=lambda x: x[0].count(os.sep))
        for old_path, new_path in subfolder_renames_sorted:
            if old_path != new_path:
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                if os.path.exists(new_path):
                    for item in os.listdir(old_path):
                        shutil.move(os.path.join(old_path, item), new_path)
                    os.rmdir(old_path)
                else:
                    os.rename(old_path, new_path)

        for track in track_list:
            subfolder = track.get("subfolder", {})
            filename = track.get("filename", "")  # Get the original filename
            titles = track.get("titles", {})
            album_titles = track.get("album_title", {})
            track_number = track.get("track_number", 1)
            contributing_artists = track.get("contributing_artists", {})
            album_artists = track.get("album_artists", {})
            genre = track.get("genre", "")

            subfolder_name = subfolder.get(self._current_language, "")
            title = titles.get(self._current_language, "")
            album_title = album_titles.get(self._current_language, "")
            contributing_artist = contributing_artists.get(self._current_language, "")
            album_artist = album_artists.get(self._current_language, "")

            if subfolder_name:
                subfolder_parts = subfolder_name.split('/')
                subfolder_path = os.path.join(extras_dir, *subfolder_parts)
            else:
                subfolder_path = extras_dir

            if not os.path.exists(subfolder_path):
                continue

            source_file = None
            if filename:
                possible_source = os.path.join(subfolder_path, filename)
                if os.path.exists(possible_source):
                    source_file = possible_source
                else:
                    for file in os.listdir(subfolder_path):
                        if file.endswith('.flac'):
                            audio = FLAC(os.path.join(subfolder_path, file))
                            if 'tracknumber' in audio and str(audio['tracknumber'][0]) == str(track_number):
                                source_file = os.path.join(subfolder_path, file)
                                break

            if not source_file:
                continue

            new_filename = filename
            if title:
                ext = os.path.splitext(filename)[1]
                new_filename = f"{title}{ext}"

            dest_file = os.path.join(subfolder_path, new_filename)
            
            # Rename the file if necessary
            if source_file != dest_file:
                if os.path.exists(dest_file):
                    os.remove(dest_file)
                os.rename(source_file, dest_file)

            audio = FLAC(dest_file)
            audio["title"] = title
            audio["album"] = album_title
            audio["tracknumber"] = str(track_number)
            audio["artist"] = contributing_artist
            audio["albumartist"] = album_artist
            audio["genre"] = genre
            audio.save()
            files_renamed += 1

        if files_renamed == 0:
            return f"Error: No matching files found for {self.albums['Extras'][self._current_language]}"
        self.coverImageChanged.emit()
        return f"Files renamed successfully for {self.albums['Extras'][self._current_language]}"

    @Property(str, notify=albumsChanged)
    def current_album_title(self):
        return self.albums[self._current_album][self._current_language]

    @Property(list, notify=albumsChanged)
    def current_track_list(self):
        return self.albums[self._current_album]["Tracks"][self._current_language]

    @Slot()
    def refresh_album_list(self):
        self.albumsChanged.emit()

    @Property(bool, notify=None)
    def include_track_numbers(self):
        return self._include_track_numbers

    @Slot(bool)
    def set_include_track_numbers(self, value):
        self._include_track_numbers = value

def main():
    runtime_root = _get_runtime_root_dir()
    resources_dir = _get_app_resources_dir()
    try:
        # Prefer Cocoa platform explicitly on macOS
        if sys.platform == 'darwin':
            os.environ.setdefault('QT_QPA_PLATFORM', 'cocoa')

        plugin_roots = [
            os.path.join(runtime_root, 'PySide6', 'Qt', 'plugins'),
            os.path.join(resources_dir, 'PySide6', 'Qt', 'plugins'),
            os.path.join(runtime_root, 'Qt', 'plugins'),
            os.path.join(resources_dir, 'Qt', 'plugins'),
        ]
        qml_roots = [
            os.path.join(runtime_root, 'PySide6', 'Qt', 'qml'),
            os.path.join(resources_dir, 'PySide6', 'Qt', 'qml'),
        ]

        existing_plugin_path = os.environ.get('QT_PLUGIN_PATH', '')
        merged_plugin_path = os.pathsep.join([
            *(p for p in plugin_roots if os.path.isdir(p)),
            *(existing_plugin_path.split(os.pathsep) if existing_plugin_path else []),
        ])
        if merged_plugin_path:
            os.environ['QT_PLUGIN_PATH'] = merged_plugin_path

        for root in plugin_roots:
            platforms_dir = os.path.join(root, 'platforms')
            if os.path.isdir(platforms_dir):
                os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', platforms_dir)
                break

        existing_qml_path = os.environ.get('QML2_IMPORT_PATH', '')
        merged_qml_path = os.pathsep.join([
            *(p for p in qml_roots if os.path.isdir(p)),
            *(existing_qml_path.split(os.pathsep) if existing_qml_path else []),
        ])
        if merged_qml_path:
            os.environ['QML2_IMPORT_PATH'] = merged_qml_path
    except Exception as e:
        debug_logger.error(f"Failed to configure Qt environment: {e}")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    debug_logger.info("Starting GUI application...")

    if getattr(sys, 'frozen', False):
        debug_logger.info(f"Running as frozen application. runtime_root={runtime_root}, resources_dir={resources_dir}")
    else:
        debug_logger.info(f"Running as script. runtime_root={runtime_root}")

    debug_logger.info(f"QT_PLUGIN_PATH={os.environ.get('QT_PLUGIN_PATH', '')}")
    debug_logger.info(f"QT_QPA_PLATFORM_PLUGIN_PATH={os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH', '')}")
    debug_logger.info(f"QML2_IMPORT_PATH={os.environ.get('QML2_IMPORT_PATH', '')}")
    debug_logger.info(f"Qt library paths: {app.libraryPaths()}")
    try:
        debug_logger.info(f"QLibraryInfo PluginsPath: {QLibraryInfo.path(QLibraryInfo.PluginsPath)}")
        debug_logger.info(f"QLibraryInfo LibraryExecutablesPath: {QLibraryInfo.path(QLibraryInfo.LibraryExecutablesPath)}")
        debug_logger.info(f"QLibraryInfo QmlImportsPath: {QLibraryInfo.path(QLibraryInfo.QmlImportsPath)}")
        debug_logger.info(f"QLibraryInfo LibrariesPath: {QLibraryInfo.path(QLibraryInfo.LibrariesPath)}")
    except Exception as e:
        debug_logger.warning(f"Failed to query QLibraryInfo paths: {e}")

    # Force Qt to look for plugins in the bundle (PyInstaller/PySide6 layouts)
    if getattr(sys, 'frozen', False):
        plugin_candidates = [
            os.path.join(runtime_root, 'PySide6', 'Qt', 'plugins'),
            os.path.join(runtime_root, 'Qt', 'plugins'),
            os.path.join(runtime_root, 'plugins'),
            # macOS .app Resources path
            os.path.join(resources_dir, 'PySide6', 'Qt', 'plugins'),
            os.path.join(resources_dir, 'Qt', 'plugins'),
            os.path.join(resources_dir, 'plugins'),
        ]
        for p in plugin_candidates:
            if os.path.isdir(p):
                app.addLibraryPath(p)
                debug_logger.info(f"Added plugin path: {p}")
        debug_logger.info(f"Qt library paths (post-add): {app.libraryPaths()}")

        # On macOS, if the FFmpeg multimedia plugin is not present, fall back to AVFoundation
        if sys.platform == 'darwin':
            mm_dirs = [os.path.join(p, 'multimedia') for p in plugin_candidates]
            ffmpeg_plugin_names = [
                'libqtmedia_ffmpeg.dylib',           # Qt6 FFmpeg backend
                'libqffmpegmediaplugin.dylib',       # Older naming
                'libffmpegmediaplugin.dylib',        # Fallback naming just in case
                'ffmpegmediaplugin.dylib',
            ]
            ffmpeg_present = any(
                os.path.exists(os.path.join(d, n)) for d in mm_dirs for n in ffmpeg_plugin_names if os.path.isdir(d)
            )
            if not ffmpeg_present:
                os.environ['QT_MEDIA_BACKEND'] = 'darwin'
                debug_logger.info("FFmpeg multimedia plugin not found; forcing QT_MEDIA_BACKEND=darwin (AVFoundation)")

    icon_path = os.path.join(resources_dir, "icon.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    if DEBUG_MODE:
        os.environ['QML_DEBUG_MESSAGES'] = '1'
        debug_logger.info("QML debugging enabled")

    engine = QQmlApplicationEngine()
    for qml_root in [
        os.path.join(runtime_root, 'PySide6', 'Qt', 'qml'),
        os.path.join(resources_dir, 'PySide6', 'Qt', 'qml'),
    ]:
        if os.path.isdir(qml_root):
            engine.addImportPath(qml_root)
            debug_logger.info(f"Added QML import path: {qml_root}")
    debug_logger.info("QML Engine created")
    
    renamer = RenamerBackend()
    engine.rootContext().setContextProperty("renamer", renamer)
    debug_logger.info("RenamerBackend initialized and set as context property")
    
    qml_file = os.path.join(resources_dir, "main.qml")
    debug_logger.info(f"Loading QML file: {qml_file}")
    
    engine.load(QUrl.fromLocalFile(qml_file))
    try:
        for warning in engine.warnings():
            debug_logger.warning(str(warning))
    except Exception:
        pass
    
    if not engine.rootObjects():
        debug_logger.error(f"Failed to load QML file: {qml_file}")
        return -1
    
    window = engine.rootObjects()[0]
    window.setProperty("iconPath", QUrl.fromLocalFile(icon_path))
    debug_logger.info("Application window created and configured")
    
    return app.exec()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()