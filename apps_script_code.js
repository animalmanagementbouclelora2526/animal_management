/**
 * Google Apps Script Web App Endpoint for Hardware Synchronization
 * 
 * Includes real-time email notifications for:
 * 1. Alert cases (new or updated alerts)
 * 2. Animal reported deceased (MORT)
 * 3. Animal transfers / sales (VENDU) when ownership changes:
 *    - If previous status was MORT: sends email to old breeder, new breeder, and admins.
 *    - If previous status was NOT MORT: sends email to admins only (just the admin).
 * 4. New animal registration
 * 
 * Safe for hardware-specific strings like "EMPTY" and lowercase "mort".
 * 
 * Instructions:
 * 1. Open your Google Sheet (Animal_management).
 * 2. Go to Extensions > Apps Script.
 * 3. Delete any existing code and paste this code.
 * 4. Click Save (Disk icon).
 * 5. Click "Deploy" > "Manage deployments".
 * 6. Click the pencil icon next to the active deployment.
 * 7. Choose "New version" in the Version dropdown.
 * 8. Click "Deploy".
 */

function doGet(e) {
  try {
    var id = e.parameter.ID;
    var mac = e.parameter.MAC;
    var category = e.parameter.Category || "Bovin";
    var gender = e.parameter.Gender || "Male";
    var birthDate = e.parameter.BirthDate || "2020-01-01";
    var vaccines = e.parameter.Vaccines || "None";
    var lat = e.parameter.Lat || "0.0";
    var lon = e.parameter.Lon || "0.0";
    var battery = e.parameter.Battery || "100";
    var alertVal = e.parameter.Alert || "None";
    var status = e.parameter.Status || "ACTIVE";
    var farmerId = e.parameter.FarmerID || "";
    var lastSync = e.parameter.LastSync || "";

    if (!mac) {
      return ContentService.createTextOutput("Error: Missing MAC Address (MAC parameter)");
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var animalSheet = ss.getSheetByName("Animal");
    var usersSheet = ss.getSheetByName("Users");
    var alertsSheet = ss.getSheetByName("alerts_history");

    if (!animalSheet) {
      return ContentService.createTextOutput("Error: 'Animal' worksheet not found in Google Sheet.");
    }

    // Find if animal exists
    var data = animalSheet.getDataRange().getValues();
    var existingRowIdx = -1;
    var oldAlert = "None";
    var oldStatus = "ACTIVE";
    var oldFarmerId = "";

    for (var i = 1; i < data.length; i++) {
      if (String(data[i][1]).trim() === String(mac).trim()) {
        existingRowIdx = i + 1; // 1-indexed row number
        oldAlert = String(data[i][9] || "None").trim();
        oldStatus = String(data[i][10] || "ACTIVE").trim();
        oldFarmerId = String(data[i][11] || "").trim();
        break;
      }
    }

    var now = new Date();
    var dateStr = Utilities.formatDate(now, Session.getScriptTimeZone() || "GMT+1", "yyyy-MM-dd HH:mm:ss");

    // Standardize input values to handle case-insensitivity and "EMPTY" values
    var cleanAlert = alertVal.trim();
    var isAlertEmpty = (cleanAlert === "" || cleanAlert.toUpperCase() === "NONE" || cleanAlert.toUpperCase() === "EMPTY");

    var currentStatus = status.toUpperCase().trim();
    var previousStatus = oldStatus.toUpperCase().trim();

    var cleanFarmerId = String(farmerId).trim();
    var cleanOldFarmerId = String(oldFarmerId).trim();

    // Check notification flags
    var isNewAnimal = false;
    var isNewAlert = false;
    var isMortAlert = false;
    var isTransferOrSale = false;
    var isTransferMort = false;
    var isSaleVendu = false;

    // Check Alert Case: must not be an empty/none/EMPTY placeholder, and must differ from previous alert
    if (!isAlertEmpty && cleanAlert !== oldAlert) {
      isNewAlert = true;
    }

    if (existingRowIdx !== -1) {
      // Check Deceased (MORT) Case
      if (previousStatus !== "MORT" && currentStatus === "MORT") {
        isMortAlert = true;
      }

      // Check Ownership Change (Transfer or Sale)
      if (cleanFarmerId !== "" && cleanOldFarmerId !== "" && cleanOldFarmerId.toUpperCase() !== "NONE" && cleanFarmerId !== cleanOldFarmerId) {
        isTransferOrSale = true;
        if (previousStatus === "MORT") {
          isTransferMort = true;
        } else {
          isSaleVendu = true;
        }
      }
    } else {
      // Animal did not exist, so it is a new animal registration
      isNewAnimal = true;
    }

    var isOwnerOrValidTransfer = false;
    if (existingRowIdx === -1) {
      isOwnerOrValidTransfer = true;
    } else {
      if (cleanFarmerId === cleanOldFarmerId || cleanOldFarmerId === "" || cleanOldFarmerId.toUpperCase() === "NONE") {
        isOwnerOrValidTransfer = true;
      } else if (previousStatus === "MORT" || previousStatus === "VENDU") {
        isOwnerOrValidTransfer = true;
      }
    }

    // Update or append animal row
    if (existingRowIdx !== -1) {
      if (isOwnerOrValidTransfer) {
        // Update existing row
        // Columns: ID (1), MAC (2), Category (3), Gender (4), Birth_date (5), Vaccines (6), Latitude (7), Longitude (8), Battery_status (9), Aler_Hist (10), Animal_status (11), Farmer_ID (12), Last_Sync (13)
        animalSheet.getRange(existingRowIdx, 3).setValue(category);
        animalSheet.getRange(existingRowIdx, 4).setValue(gender);
        animalSheet.getRange(existingRowIdx, 5).setValue(birthDate);
        animalSheet.getRange(existingRowIdx, 6).setValue(vaccines);
        animalSheet.getRange(existingRowIdx, 7).setValue(lat);
        animalSheet.getRange(existingRowIdx, 8).setValue(lon);
        animalSheet.getRange(existingRowIdx, 9).setValue(battery);

        // Ownership Transfer resets status to ACTIVE as per app.py
        var newStatus = isTransferOrSale ? "ACTIVE" : status;

        animalSheet.getRange(existingRowIdx, 10).setValue(alertVal);
        animalSheet.getRange(existingRowIdx, 11).setValue(newStatus);
        if (farmerId) {
          animalSheet.getRange(existingRowIdx, 12).setValue(farmerId);
        }
        animalSheet.getRange(existingRowIdx, 13).setValue(dateStr);
      }
    } else {
      // Append new row
      var newId = data.length;
      if (id) {
        newId = id;
      }
      animalSheet.appendRow([
        newId,
        mac,
        category,
        gender,
        birthDate,
        vaccines,
        lat,
        lon,
        battery,
        alertVal,
        status,
        farmerId,
        dateStr
      ]);
    }

    // Fetch user/admin emails
    var breederEmail = "";
    var prevBreederEmail = "";
    var adminEmails = [];

    if (usersSheet) {
      var usersData = usersSheet.getDataRange().getValues();
      for (var j = 1; j < usersData.length; j++) {
        var row = usersData[j];
        var userId = String(row[0]).trim(); // Eleveur_ID
        var role = String(row[3]).trim().toLowerCase(); // Role
        var email = String(row[4]).trim(); // Email

        if (farmerId && userId === String(farmerId).trim()) {
          breederEmail = email;
        }
        if (oldFarmerId && userId === oldFarmerId) {
          prevBreederEmail = email;
        }
        if (role === "admin" && email) {
          adminEmails.push(email);
        }
      }
    }

    // ----------------------------------------------------
    // Scenario 1: New Alert Case
    // ----------------------------------------------------
    if (isNewAlert) {
      // 1. Log alert to alerts_history
      if (alertsSheet) {
        var alertData = alertsSheet.getDataRange().getValues();
        var alertId = alertData.length;
        alertsSheet.appendRow([
          alertId,
          mac,
          alertVal,
          lat,
          lon,
          dateStr
        ]);
      }

      var alertSubject = "Animal Alert";
      var alertBody = "Animal : " + mac + "\n\n" +
        "Alert :\n" + alertVal + "\n\n" +
        "Battery :\n" + battery + " %\n\n" +
        "Position :\nhttps://www.google.com/maps?q=" + lat + "," + lon + "\n\n" +
        "Date :\n" + dateStr + "\n";

      if (breederEmail) {
        sendEmailSafely(breederEmail, alertSubject, alertBody);
      }
      for (var k = 0; k < adminEmails.length; k++) {
        sendEmailSafely(adminEmails[k], alertSubject, alertBody);
      }
    }

    // ----------------------------------------------------
    // Scenario 2: Deceased Case (MORT)
    // ----------------------------------------------------
    if (isMortAlert) {
      var mortSubject = "Animal Reported Deceased (MORT)";
      var mortBody = "Animal MAC " + mac + " has been reported as deceased (status changed to MORT) by breeder " + farmerId + " on " + dateStr + ".";

      if (breederEmail) {
        sendEmailSafely(breederEmail, mortSubject, mortBody);
      }
      for (var k = 0; k < adminEmails.length; k++) {
        sendEmailSafely(adminEmails[k], mortSubject, mortBody);
      }
    }

    // ----------------------------------------------------
    // Scenario 3: Ownership Transfer / Sale (VENDU)
    // ----------------------------------------------------
    if (isTransferOrSale) {
      if (isTransferMort) {
        // Transferred because previous status was MORT - notify both breeders & admin
        var transferSubject = "Animal transfer";
        var transferBody = "Animal " + mac + "\n\ntransferred to farmer " + farmerId + "\n\nbecause previous status was MORT.\n";

        if (breederEmail) {
          sendEmailSafely(breederEmail, transferSubject, transferBody);
        }
        if (prevBreederEmail) {
          sendEmailSafely(prevBreederEmail, transferSubject, transferBody);
        }
        for (var k = 0; k < adminEmails.length; k++) {
          sendEmailSafely(adminEmails[k], transferSubject, transferBody);
        }
      } else if (isSaleVendu) {
        // Sale transfer (Status of existing animal was not MORT) - notify Admin ONLY
        var saleSubject = "Animal Sale / Duplicate Registration Attempt";
        var saleBody = "Breeder " + farmerId + " attempted to register MAC " + mac + ",\n" +
          "which was already registered to Breeder " + oldFarmerId + ".\n" +
          "Previous Animal Status: " + oldStatus + "\n" +
          "Date: " + dateStr + "\n";

        for (var k = 0; k < adminEmails.length; k++) {
          sendEmailSafely(adminEmails[k], saleSubject, saleBody);
        }
      }
    }

    // ----------------------------------------------------
    // Scenario 4: New Animal Registration Case
    // ----------------------------------------------------
    if (isNewAnimal) {
      var newAnimalSubject = "New Animal Registered";
      var newAnimalBody = "A new animal has been registered in the system:\n\n" +
        "MAC: " + mac + "\n" +
        "Category: " + category + "\n" +
        "Gender: " + gender + "\n" +
        "Birth Date: " + birthDate + "\n" +
        "Vaccines: " + vaccines + "\n" +
        "Breeder ID: " + farmerId + "\n" +
        "Date: " + dateStr + "\n";

      if (breederEmail) {
        sendEmailSafely(breederEmail, newAnimalSubject, newAnimalBody);
      }
      for (var k = 0; k < adminEmails.length; k++) {
        sendEmailSafely(adminEmails[k], newAnimalSubject, newAnimalBody);
      }
    }

    return ContentService.createTextOutput("Sync completed successfully!");
  } catch (globalErr) {
    return ContentService.createTextOutput("Error executing script: " + globalErr.message);
  }
}

function sendEmailSafely(recipient, subject, body) {
  try {
    MailApp.sendEmail(recipient, subject, body);
  } catch (err) {
    console.error("Failed to send email to " + recipient + ": " + err.message);
  }
}
