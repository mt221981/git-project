<div dir="rtl">

# העלאת הפרויקט ל-GitHub

## שלב 1: יצירת Repository ב-GitHub

1. **היכנס ל-GitHub**:
   - לך ל-https://github.com
   - התחבר לחשבון שלך (או צור חשבון חדש)

2. **צור Repository חדש**:
   - לחץ על הכפתור **"+"** בפינה הימנית העליונה
   - בחר **"New repository"**

3. **הגדר את ה-Repository**:
   - **Repository name**: `legal-content-system` (או כל שם אחר)
   - **Description**: מערכת מקצה-לקצה לעיבוד פסקי דין ויצירת תוכן SEO
   - **Visibility**:
     - 🔒 **Private** (מומלץ אם הפרויקט פרטי)
     - 🌍 **Public** (אם אתה רוצה לשתף עם אחרים)
   - ❌ **אל תסמן**:
     - "Add a README file"
     - "Add .gitignore"
     - "Choose a license"
     (כבר יש לנו את הקבצים האלה!)

4. **לחץ על "Create repository"**

## שלב 2: חיבור Repository המקומי ל-GitHub

אחרי שיצרת את ה-repository ב-GitHub, תראה מסך עם הוראות. **עקוב אחרי השורות האלה**:

### אופציה: Push an existing repository from the command line

פתח terminal/command prompt בתיקיית הפרויקט והרץ:

</div>

```bash
# נווט לתיקיית הפרויקט
cd "C:\Users\MOSHE-LT-LAW\Desktop\first try\legal-content-system"

# הוסף את GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/legal-content-system.git

# שנה את שם ה-branch ל-main (אם צריך)
git branch -M main

# העלה את הקוד ל-GitHub
git push -u origin main
```

<div dir="rtl">

**החלף** `YOUR_USERNAME` בשם המשתמש שלך ב-GitHub!

### אם יש לך אימות 2FA או שצריך סיסמה

GitHub לא מקבל יותר סיסמאות רגילות ב-command line. תצטרך:

**אופציה 1: Personal Access Token (מומלץ)**
1. לך ל-Settings → Developer settings → Personal access tokens → Tokens (classic)
2. לחץ "Generate new token (classic)"
3. תן לו שם (למשל "legal-content-system")
4. בחר את ההרשאות: `repo` (כל תיבות הסימון)
5. לחץ "Generate token"
6. **העתק את ה-token** (לא תוכל לראות אותו שוב!)
7. בעת ה-push, השתמש ב-token במקום סיסמה:
   - Username: YOUR_USERNAME
   - Password: THE_TOKEN_YOU_COPIED

**אופציה 2: SSH**
אם אתה מעדיף SSH, תצטרך להגדיר SSH keys (מורכב יותר).

## שלב 3: ודא שהכל הועלה

</div>

```bash
# בדוק שה-remote הוגדר נכון
git remote -v
# אמור להראות:
# origin  https://github.com/YOUR_USERNAME/legal-content-system.git (fetch)
# origin  https://github.com/YOUR_USERNAME/legal-content-system.git (push)

# בדוק את הסטטוס
git status
# אמור להראות: "Your branch is up to date with 'origin/main'"
```

<div dir="rtl">

לך ל-https://github.com/YOUR_USERNAME/legal-content-system ותראה את כל הקבצים שלך!

## שלב 4: שינויים עתידיים

בכל פעם שתעשה שינויים בפרויקט:

</div>

```bash
# הוסף קבצים שהשתנו
git add .

# צור commit עם הודעה
git commit -m "תיאור השינוי"

# העלה ל-GitHub
git push
```

<div dir="rtl">

## שלב 5 (אופציונלי): Clone בכדי לעבוד ממחשב אחר

אם אתה רוצה להוריד את הפרויקט במחשב אחר:

</div>

```bash
git clone https://github.com/YOUR_USERNAME/legal-content-system.git
cd legal-content-system
```

<div dir="rtl">

## בעיות נפוצות

### שגיאה: "Permission denied"
- ודא שהשתמשת ב-Personal Access Token נכון
- או הגדר SSH keys

### שגיאה: "Repository not found"
- ודא ש-USERNAME נכון
- ודא שה-repository נוצר ב-GitHub

### שגיאה: "Updates were rejected"

</div>

```bash
# אם מישהו עשה שינויים ב-GitHub, תחילה משוך:
git pull origin main
# ואז push:
git push
```

<div dir="rtl">

## סטטוס נוכחי

✅ Git repository initialized locally
✅ All files committed (101 files, 16,758+ lines)
✅ Initial commit created with comprehensive message
✅ .gitignore configured (excludes temp files, secrets, node_modules)
✅ LICENSE file added (MIT License)

**מה שנשאר לעשות**:
1. יצירת repository ב-GitHub (online)
2. חיבור ה-repository המקומי ל-GitHub
3. העלאת הקוד (git push)

## קובץ README.md

ה-README.md בפרויקט כולל:
- ✅ תיאור מקיף של המערכת (עברית + אנגלית)
- ✅ הוראות התקנה (Backend + Frontend)
- ✅ תיעוד כל 7 השלבים
- ✅ דוגמאות שימוש
- ✅ מפרט טכני
- ✅ הוראות deployment

## קישורים שימושיים

- **GitHub Docs**: https://docs.github.com/en/get-started/quickstart
- **Personal Access Tokens**: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- **SSH Keys Setup**: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

**זקוק לעזרה?** פתח issue ב-GitHub אחרי ההעלאה או שאל שאלות!

**Good luck! בהצלחה!** 🚀

</div>
