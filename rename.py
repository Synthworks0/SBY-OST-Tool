import multiprocessing
import os
import shutil
import sys
import json
import time
import tempfile
from mutagen.flac import FLAC
from PySide6.QtCore import QObject, Slot, Property, Signal, QUrl, QDir, QTimer, QThread
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QFileSystemModel
from PySide6.QtGui import QIcon
from PySide6.QtCore import QResource

# Track lists for each album in Japanese, Romaji, and English

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
                "Seishun Buta Yarou", "Mai-san", "Kappuru", "Suiheisen", "Daiji na Koto", "Hentai", "Enoshima", "Hosho", "Ibunshi", "Toshi Densetsu",
                "Kizu", "Tasukete Kure", "Oomajime", "Usukimiwarui Kuukan", "Hitori", "Higashihama Kaisuiyokujou", "Baka Sakuta!", "Koushite, Sekai wa Sakurajima Mai wo Torimodoshita", "Asa desu...", "Ninjagokko",
                "Futaba", "Otome Chikku", "Kenokan", "Uchiage Hanabi", "Juwaki no Mukou", "2 Kaime", "Pink no Bikini", "Otomegokoro", "Irekawatta Shimai", "Wadakamari",
                "Hatsukoi no Hito"
            ],
            "English": [
                "Rascal", "Mai-san", "Couple", "Horizon", "Important Thing", "Pervert", "Enoshima", "Guarantee", "Alien", "Urban Legend",
                "Scar", "Help Me", "Serious", "Creepy Space", "Alone", "Higashihama Beach", "Stupid Sakuta!", "Thus, the World Regained Mai Sakurajima", "It's Morning...", "Playing Ninja",
                "Futaba", "Girly", "Disgust", "Fireworks", "On the Other Side of the Receiver", "Second Time", "Pink Bikini", "A Girl's Feelings", "Swapped Sisters", "Ill Feelings",
                "First Love"
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
                "生きることを選んだから", "小さな可能性のために", "もう一度", "満ち足りた顔", "静かな空気", "「さすが、梓川はブタ野郎だね」", "大切な名前", "不可思議のカルテ movie ver.", "不可思議のカルテ"
            ],
            "Romaji": [
                "Seishun Buta Yarou wa Yumemiru Shoujo no Yume wo Minai", "'Arigatou' to 'Ganbatta ne' to 'Daisuki'", "Yume no Sugata", "Kakitai Koto", "Kinou no Kore", "Yume no Naka", "Deeto ~Yume no Sekai~", "Slow Motion", "Ketsui no Hikari",
                "Massugu na Omoi", "Tsurai Sentaku", "Igai na Kotoba", "Unmei wo Wakeru Jikan", "Kanashimi", "Eranda Michi", "Fuan no Kajitsu", "Baka na Koto", "Kono Yakusoku wo Mamoru Tame ni", "'Tadaima' 'Okaerinasai'",
                "Ikiru Koto wo Eranda kara", "Chiisana Kanousei no Tame ni", "Mou Ichido", "Michitarita Kao", "Shizuka na Kuuki", "'Sasuga, Azusagawa wa Buta Yarou da ne'", "Taisetsu na Namae", "Fukashigi no Karte movie ver.", "Fukashigi no Karte"
            ],
            "English": [
                "Rascal Does Not Dream of a Dreaming Girl", "'Thank You', 'You Did Well', and 'I Love You'", "Dream Figure", "What I Want to Write", "Yesterday's This", "In A Dream", "Date ~Dream World~", "Slow Motion", "Light of Determination",
                "Straight Feelings", "Painful Choice", "Unexpected Words", "Time to Divide Fate", "Sadness", "The Road of Choice", "The Fruit of Anxiety", "Stupid Thing", "To Keep This Promise", "'I'm home' 'Welcome back'",
                "Because I Chose to Live", "For Small Possibilities", "Once Again", "Satisfied Face", "Quiet Air", "'Nothing less from you, Azusagawa. Such a rascal'", "Important Name", "Fukashigi no Karte movie ver.", "Fukashigi no Karte"
            ]
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
                "戸惑い", "泣いた分と同じだけ嬉しかった", "花楓の成長", "自分で決めた道", "夢の続き", "不可思議のカルテ 花楓&かえで Ver", "不可思議のカルテ 梓川 花楓Ver",
                "ミューズになっちゃう", "オトメノート", "ミューズになっちゃう(Instrumental)", "オトメノート(Instrumental)"
            ],
            "Romaji": [
                "Kimyou na Yume", "Nostalgia", "Yarikirenai Omoi", "Hisokana Yorokobi", "Odoru Kimochi", "Kaede no Onegai", "Moshikashite", "Kaede no Tame ni", "Utatane", "Nokku wa Shita",
                "Gohoubi-", "Fuan to Kinchou", "Ganbareru kara", "Ippo Zutsu", "Kokochi no Ii Asa", "Soredemo Shinpai", "Maiagaru Sakuta", "Fuan na Shirase", "Tomaranai Kowasa", "Kaede no Yume",
                "Tomadoi", "Naita Bun to Onaji Dake Ureshikatta", "Kaede no Seichou", "Jibun de Kimeta Michi", "Yume no Tsuzuki", "Fukashigi no Karte Kaede & Kaede Ver", "Fukashigi no Karte Azusagawa Kaede Ver",
                "Myuuzu ni Nacchau", "Otome Noto", "Myuuzu ni Nacchau (Instrumental)", "Otome Noto (Instrumental)"
            ],
            "English": [
                "Strange Dream", "Nostalgia", "Unbearable Feelings", "Secret Joy", "Dancing Feelings", "Kaede's Request", "Maybe", "For Kaede", "Nap", "Knocked",
                "Reward", "Anxiety and Tension", "Because I Can Do It", "Step by Step", "Comfortable Morning", "Still Worried", "Excited Sakuta", "Anxious News", "Unstoppable Fear", "Kaede's Dream",
                "Confusion", "As Happy as I Cried", "Kaede's Growth", "The Path I Chose", "Continuation of the Dream", "Fukashigi no Karte Kaede & Kaede Ver", "Fukashigi no Karte Azusagawa Kaede Ver",
                "Becoming a Muse", "Otome Note", "Becoming a Muse (Instrumental)", "Otome Note (Instrumental)"
            ]
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
                "安心", "頑張ったから", "家族", "見えない謎", "入学おめでとう", "不可思議のカルテ (All Heroine Ver.)", "不可思議のカルテ (梓川咲太 Ver.)", "不可思議のカルテ (Juvenile Ver.)"
            ],
            "Romaji": [
                "Onaji Yume", "Daiji na Mono", "Omamori", "Oyakusoku", "Kaede no Negai", "Kangaegoto", "Chinmoku no Ame", "Saikai", "Shiawase na Jikan",
                "Sakuta no Shishunki Shoukougun", "Issho ni Kaeru", "Takamaru Fuan", "Iwakan", "Utagai", "Sakuta no Kesshin", "Doushitemo", "Mou Sukoshi no Shinbou", "Omamori to Yakusoku", "Mai no Yasashisa",
                "Anshin", "Ganbatta kara", "Kazoku", "Mienai Nazo", "Nyugaku Omedetou", "Fukashigi no Karte (All Heroine Ver.)", "Fukashigi no Karte (Azusagawa Sakuta Ver.)", "Fukashigi no Karte (Juvenile Ver.)"
            ],
            "English": [
                "Same Dream", "Important Thing", "Amulet", "Promise", "Kaede's Wish", "Thoughts", "Silent Rain", "Reunion", "Happy Time",
                "Sakuta's Puberty Syndrome", "Going Home Together", "Rising Anxiety", "Discomfort", "Doubt", "Sakuta's Determination", "No Matter What", "A Little More Patience", "Amulet and Promise", "Mai's Kindness",
                "Relief", "Because I Tried", "Family", "Invisible Mystery", "Congratulations on Your Admission", "Fukashigi no Karte (All Heroine Ver.)", "Fukashigi no Karte (Azusagawa Sakuta Ver.)", "Fukashigi no Karte (Juvenile Ver.)"
            ]
        }
    }
}

class Renamer:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = os.path.join(base_path, "resources", "SBY Soundtracks")
        self.albums = albums
        self.qml_path = os.path.join(base_path, "main.qml")

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
                            
                            # Update metadata
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

    def __init__(self):
        super().__init__()
        self._current_album = list(self.albums.keys())[0]
        self._current_language = "English"
        self._output_folder = ""
        self._current_path = ""
        self._folder_contents = []
        self._drive_list = []
        self._album_states = {album: "extract" for album in self.albums}
        self.load_last_output_folder()
        QTimer.singleShot(0, self.initialize_file_system)

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
            print(f"Error saving config: {str(e)}")

    def load_last_output_folder(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                last_folder = config.get('last_output_folder', '')
                self.set_output_folder(last_folder)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading config: {str(e)}")

    @Slot(str)
    def set_output_folder(self, folder):
        if self._output_folder != folder:
            self._output_folder = folder
            self.outputFolderChanged.emit()
            self.save_last_output_folder()
            self.check_and_create_soundtracks()
            self.canExtractChanged.emit()

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
        destination_dir = os.path.join(self._output_folder, "SBY Soundtracks", self.albums[album_name]["English"])

        if not os.path.exists(source_dir):
            self.extractionFinished.emit(f"Error: Soundtrack '{album_name}' not found")
            return

        try:
            os.makedirs(destination_dir, exist_ok=True)
            files = os.listdir(source_dir)

            for i, file in enumerate(files):
                source_file = os.path.join(source_dir, file)
                dest_file = os.path.join(destination_dir, file)
                shutil.copy2(source_file, dest_file)

            self._album_states[album_name] = "rename"
            self.albumStateChanged.emit()
            self.extractionFinished.emit(f"Soundtrack '{album_name}' extracted successfully")
            
            self.set_current_album(album_name)
            self.rename_files()
        except Exception as e:
            self.extractionFinished.emit(f"Error extracting soundtrack: {str(e)}")

    @Slot(result=bool)
    def can_extract(self):
        return bool(self._output_folder)

    @Slot(result=str)
    def get_current_album_state(self):
        return self._album_states.get(self._current_album, "extract")

    def get_resource_path(self, *paths):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, "resources", *paths)

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

    @Slot(str)
    def set_current_language(self, language):
        self.current_language = language

    @Slot(result=str)
    def rename_files(self):
        try:
            album_dir = os.path.join(self._output_folder, "SBY Soundtracks", self.albums[self._current_album]["English"])
            if not os.path.exists(album_dir) or len(os.listdir(album_dir)) == 0:
                return f"Error: No files found for {self.albums[self._current_album][self._current_language]}"
            
            track_names = self.albums[self._current_album]["Tracks"][self._current_language]
            files_renamed = 0

            for i, new_name in enumerate(track_names, 1):
                for file in os.listdir(album_dir):
                    if file.endswith(".flac"):
                        old_path = os.path.join(album_dir, file)
                        audio = FLAC(old_path)
                        if int(audio["tracknumber"][0]) == i:
                            new_path = os.path.join(album_dir, f"{i:02d}. {new_name}.flac")
                            os.rename(old_path, new_path)
                            
                            # Update metadata
                            audio = FLAC(new_path)
                            audio["title"] = new_name
                            audio["album"] = self.albums[self._current_album][self._current_language]
                            audio.save()
                            files_renamed += 1
                            break

            if files_renamed == 0:
                return f"Error: No matching files found for {self.albums[self._current_album][self._current_language]}"
            self.coverImageChanged.emit()
            return f"Files renamed successfully for {self.albums[self._current_album][self._current_language]}"
        except Exception as e:
            return f"Error renaming files: {str(e)}"

    @Property(str, notify=albumsChanged)
    def current_album_title(self):
        return self.albums[self._current_album][self._current_language]

    @Property(list, notify=albumsChanged)
    def current_track_list(self):
        return self.albums[self._current_album]["Tracks"][self._current_language]

    @Slot()
    def refresh_album_list(self):
        self.albumsChanged.emit()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        cli_main()
    else:
        gui_main()

def gui_main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    print("Starting GUI...")

    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "icon.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    engine = QQmlApplicationEngine()
    
    renamer = RenamerBackend()
    engine.rootContext().setContextProperty("renamer", renamer)
    
    qml_file = os.path.join(base_path, "main.qml")
    
    engine.load(QUrl.fromLocalFile(qml_file))
    
    if not engine.rootObjects():
        print(f"Failed to load QML file: {qml_file}")
        return -1
    
    window = engine.rootObjects()[0]
    window.setProperty("iconPath", QUrl.fromLocalFile(icon_path))
    
    sys.exit(app.exec())

def cli_main():
    renamer = RenamerBackend()
    print("Welcome to the SBY OST Tool")
    
    output_folder = input("Enter the output folder path: ")
    if not os.path.exists(output_folder):
        print("Output folder does not exist. Creating it...")
        os.makedirs(output_folder, exist_ok=True)
    
    renamer.set_output_folder(output_folder)
    
    while True:
        print("\nAvailable actions:")
        print("1. Extract soundtrack")
        print("2. Rename soundtrack")
        print("3. Quit")
        
        action = input("Choose an action number: ")
        
        if action == '1':
            extract_cli(renamer)
        elif action == '2':
            rename_cli(renamer)
        elif action == '3':
            break
        else:
            print("Invalid choice. Please try again.")

def extract_cli(renamer):
    print("\nAvailable albums:")
    for i, album in enumerate(renamer.albums.keys(), 1):
        print(f"{i}. {album}")
    
    album_choice = input("Choose an album number to extract: ")
    try:
        album_name = list(renamer.albums.keys())[int(album_choice) - 1]
        sby_folder = os.path.join(renamer.output_folder, "SBY Soundtracks")
        if not os.path.exists(sby_folder):
            os.makedirs(sby_folder, exist_ok=True)
        renamer.extract_soundtrack(album_name)
        print(f"Soundtrack '{album_name}' extracted successfully")
    except (ValueError, IndexError):
        print("Invalid choice. Please try again.")
    except Exception as e:
        print(f"Error extracting soundtrack: {str(e)}")

def rename_cli(renamer):
    print("\nAvailable albums:")
    for i, album in enumerate(renamer.albums.keys(), 1):
        print(f"{i}. {album}")
    
    album_choice = input("Choose an album number to rename: ")
    try:
        album_name = list(renamer.albums.keys())[int(album_choice) - 1]
        sby_folder = os.path.join(renamer.output_folder, "SBY Soundtracks")
        album_folder = os.path.join(sby_folder, renamer.albums[album_name]["English"])
        if not os.path.exists(album_folder):
            print(f"Error: Album '{album_name}' has not been extracted yet.")
            return

        print("\nAvailable languages:")
        languages = ["Japanese", "Romaji", "English"]
        for i, lang in enumerate(languages, 1):
            print(f"{i}. {lang}")
        
        lang_choice = input("Choose a language number: ")
        language = languages[int(lang_choice) - 1]
        
        renamer.set_current_album(album_name)
        renamer.set_current_language(language)
        result = renamer.rename_files()
        print(result)
    except (ValueError, IndexError):
        print("Invalid choice. Please try again.")
    except Exception as e:
        print(f"Error renaming files: {str(e)}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        cli_main()
    else:
        main()