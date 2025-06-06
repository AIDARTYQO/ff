# מדריך לשימוש בהקס אדיטור (Hex Editor)

## מה זה הקס אדיטור?

הקס אדיטור הוא כלי שמאפשר לצפות, לערוך ולנתח קבצים ברמת הבייטים – כלומר, לראות את התוכן הגולמי של כל קובץ בדיוק כפי שהוא נשמר על הדיסק. העריכה מתבצעת בייצוג הקסדצימלי (בסיס 16), ומכאן שמו.

## למה זה שימושי?

- **תיקון קבצים פגומים**  
- **הנדסה לאחור (Reverse Engineering)**
- **ניתוח פורמטים של קבצים**
- **שינוי מידע בקבצי משחקים/תוכנות**
- **חקר מערכת הקבצים עצמה**

---

## איך נראה הקס אדיטור?

בדרך כלל, החלון הראשי של כל הקס אדיטור מחולק לשלושה חלקים עיקריים:

1. **עמודת כתובות (Offset/Address):**  
   מראה את המיקום של כל שורה (כלומר, באיזה בייט מתוך הקובץ אתה נמצא).

2. **תצוגה הקסדצימלית (Hex view):**  
   כאן רואים את ערכי הבייטים עצמם, מיוצגים בבסיס 16 – לדוג' 43 A1 00 FF.

3. **תצוגה טקסטואלית (ASCII/Text view):**  
   תצוגה של אותם בייטים כאותיות באנגלית (או תווים אחרים), אם הם ניתנים להצגה.

---

## איך משתמשים בהקס אדיטור?

### 1. פתיחת קובץ:
- פתח את התוכנה (למשל HxD, Hex Workshop, או 010 Editor).
- בתפריט, בחר "File" > "Open" ובחר את הקובץ הרצוי.

### 2. ניווט בקובץ:
- תוכל לגלול או לדלג לכתובת מסוימת (Offset) כדי למצוא נתונים רלוונטיים.
- חיפוש: השתמש ב־Ctrl+F כדי לחפש ערך הקסדצימלי או טקסט.

### 3. עריכת נתונים:
- לחץ על ערך הקסדצימלי וכתוב ערך חדש (למשל, שנה 41 ל־FF).
- שים לב – כל שינוי ישפיע ישירות על הקובץ, אז מומלץ לגבות!

### 4. שמירת שינויים:
- לאחר שסיימת, לחץ "Save" או "Save As" כדי לשמור את הגרסה הערוכה.

---

## הבנת מערכת הקבצים ברמת Hex

מערכת קבצים (File System) מארגנת את הנתונים על הכונן. ניתן לראות ולנתח את מבנה מערכת הקבצים עצמה (למשל, FAT, NTFS, ext4) ב־Hex Editor, אם פותחים את הדיסק עצמו (או Image שלו, לדוג' קובץ .img).

### דוגמאות למה שרואים:

- **Boot Sector (MBR, GPT):**  
  החלק הראשון של הדיסק, כולל טבלת מחיצות ונתוני אתחול.
- **Directory Entries:**  
  רשומות שמכילות שמות קבצים, כתובות התחלה, גודל, הרשאות וכו'.
- **Data Area:**  
  המידע הגולמי של כל קובץ.

---

## מה אפשר לעשות עם זה?

1. **שחזור מידע:**  
   לאתר נתונים שנמחקו, או לשחזר קבצים מתוך image של דיסק.
2. **פתרון בעיות:**  
   תיקון ידני של שגיאות בקבצים (למשל, תיקון header של קובץ JPEG).
3. **ניתוח פורמטים:**  
   להבין איך קובץ בנוי – שימושי בפיתוח או הנדסה לאחור.
4. **שינוי והזרקת קוד:**  
   הוספת/שינוי קוד בינארי בתוכנות (מתקדם, זהירות!).
5. **בדיקת חתימות:**  
   זיהוי סוגי קבצים לפי ה־Magic Number שלהם.

---

## טיפים חשובים

- **הקפד לגבות כל קובץ לפני עריכה!**
- **לא כל עריכה תגרום לקובץ להישאר תקין – לפורמטים רבים יש CRC/סיכום בדיקה.**
- **לימוד פורמט הקובץ או מערכת הקבצים מראש יקצר תהליכים.**
- **אפשר למצוא דוקומנטציה בפורומים ואתרים כמו [File Signatures Table](https://www.filesignatures.net/), [Forensics Wiki](https://forensics.wiki/) ועוד.**

---

## המלצות לתוכנות חינמיות:

- **HxD** (Windows) – פשוטה וחזקה
- **wxHexEditor** (Linux, Mac, Windows)
- **010 Editor** (חינמית / בתשלום, עם Templates מובנים)

---

## דוגמה: זיהוי Magic Number

פותחים קובץ כלשהו ב-HxD, ורואים:
```
00000000 | 89 50 4E 47 0D 0A 1A 0A ...
```
הערכים הראשונים (89 50 4E 47) – זה ה־Magic Number של PNG.

---

אם יש לך קובץ או מערכת קבצים שתרצה לנתח יחד – אשמח לעזור שלב אחר שלב!