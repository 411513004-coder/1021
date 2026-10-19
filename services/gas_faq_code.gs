/**
 * LINE Bot FAQ 知識資料庫查詢 API (Google Apps Script)
 * 
 * 部署說明：
 * 1. 在 Google 試算表選單點選「擴充功能」->「Apps Script」
 * 2. 清空原本內容，貼上此程式碼並存檔 (Ctrl+S)
 * 3. 確保試算表的工作表名稱為「FAQ」，第一列為標題：ID | 問題 | 關鍵字 | 答案 | 啟用
 * 4. 點擊右上角「部署」->「新增部署作業」
 *    - 類型選擇：網頁應用程式 (Web App)
 *    - 執行身分：我 (Me)
 *    - 誰可以存取：所有人 (Anyone)
 * 5. 點擊「部署」並複製產生的「網頁應用程式網址」(結尾為 /exec)
 */

function doGet(e) {
  return handleFaqRequest(e);
}

function doPost(e) {
  return handleFaqRequest(e);
}

function handleFaqRequest(e) {
  try {
    var query = "";
    if (e && e.parameter && e.parameter.q) {
      query = e.parameter.q.trim();
    } else if (e && e.postData && e.postData.contents) {
      try {
        var body = JSON.parse(e.postData.contents);
        query = (body.q || body.query || "").trim();
      } catch (err) {
        query = e.postData.contents.trim();
      }
    }

    if (!query) {
      return jsonResponse({
        status: "ok",
        message: "LINE Bot FAQ 知識庫 API 正常運作中。請透過 ?q=問題 進行查詢。",
        found: false
      });
    }

    var result = searchFaq(query);
    return jsonResponse(result);

  } catch (err) {
    return jsonResponse({
      status: "error",
      message: err.toString(),
      found: false
    });
  }
}

function searchFaq(query) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("FAQ");
  if (!sheet) {
    sheet = ss.getSheets()[0]; // 預設使用第一個工作表
  }

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) {
    return { found: false, message: "FAQ 資料庫尚無資料" };
  }

  // 取得標題列與欄位索引
  var header = data[0];
  var idxQuestion = 1;
  var idxKeywords = 2;
  var idxAnswer = 3;
  var idxActive = 4;

  for (var c = 0; c < header.length; c++) {
    var title = String(header[c]).trim();
    if (title === "問題") idxQuestion = c;
    else if (title === "關鍵字") idxKeywords = c;
    else if (title === "答案") idxAnswer = c;
    else if (title === "啟用") idxActive = c;
  }

  var queryLower = query.toLowerCase();
  var bestMatch = null;
  var maxScore = 0;

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var activeVal = String(row[idxActive]).trim().toUpperCase();
    // 檢查是否啟用 (空白或 TRUE 皆視為啟用)
    if (activeVal === "FALSE" || activeVal === "否" || activeVal === "0") {
      continue;
    }

    var question = String(row[idxQuestion] || "").trim();
    var keywords = String(row[idxKeywords] || "").trim();
    var answer = String(row[idxAnswer] || "").trim();

    if (!answer) continue;

    var questionLower = question.toLowerCase();
    var currentScore = 0;

    // 1. 完全比對標準問題
    if (questionLower === queryLower) {
      currentScore += 100;
    } 
    // 2. 使用者問題包含標準問題，或標準問題包含使用者問題
    else if (queryLower.indexOf(questionLower) !== -1 || questionLower.indexOf(queryLower) !== -1) {
      currentScore += 50;
    }

    // 3. 關鍵字比對 (以逗號、頓號、空格分隔)
    if (keywords) {
      var kwList = keywords.split(/[,，、\s]+/);
      var matchedCount = 0;
      for (var k = 0; k < kwList.length; k++) {
        var kw = kwList[k].trim().toLowerCase();
        if (kw && queryLower.indexOf(kw) !== -1) {
          matchedCount++;
          currentScore += 20;
        }
      }
    }

    if (currentScore > maxScore && currentScore >= 20) {
      maxScore = currentScore;
      bestMatch = {
        found: true,
        id: String(row[0] || ""),
        matched_question: question,
        answer: answer,
        score: maxScore
      };
    }
  }

  if (bestMatch) {
    return bestMatch;
  }

  return { found: false, query: query, message: "知識庫中無適當答案" };
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
