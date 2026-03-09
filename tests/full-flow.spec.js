const { test, expect } = require('@playwright/test');

test.describe('Inspection App Full Flow', () => {
  let customerName;
  let equipmentSerial;

  // Helper function to create customer with full details
  async function createCustomerWithDetails(page, name) {
    await page.goto('/customers/new/');
    await page.fill('input[name="name"]', name);
    await page.fill('input[name="location"]', 'North Yard - Spokane');
    await page.fill('input[name="asset_id"]', `ASSET-${Date.now()}`);
    await page.fill('input[name="address_line1"]', '123 Industrial Blvd');
    await page.fill('input[name="address_line2"]', 'Suite 200');
    await page.fill('input[name="city"]', 'Spokane');
    await page.fill('input[name="state"]', 'WA');
    await page.fill('input[name="zip_code"]', '99201');
    await page.fill('input[name="phone"]', '(509) 555-1234');
    await page.fill('input[name="email"]', 'fleet@testcustomer.com');
    await page.fill('input[name="contact_person_name"]', 'John Smith');
    await page.fill('input[name="contact_person_title"]', 'Fleet Manager');
    await page.fill('input[name="contact_person_phone"]', '(509) 555-1235');
    await page.getByRole('button', { name: 'Create Customer' }).click();
    await expect(page).toHaveURL('/equipment/new/');
  }

  // Helper function to create equipment with full details including vehicle info
  async function createEquipmentWithVehicle(page, customerName, serial, makeModel = 'Altec AT37G') {
    await page.selectOption('select[name="customer"]', { label: customerName });
    await page.fill('input[name="location"]', 'Main Warehouse - Bay 3');
    await page.fill('input[name="serial_number"]', serial);

    const [make, model] = makeModel.split(' ');
    await page.fill('input[name="make"]', make);
    await page.fill('input[name="model"]', model);
    await page.fill('input[name="unit_number"]', `AERIAL-${Date.now().toString().slice(-3)}`);
    await page.fill('input[name="year_of_manufacture"]', '2020');
    await page.fill('input[name="max_working_height"]', '45');

    // Vehicle information
    await page.fill('input[name="vehicle_year"]', '2019');
    await page.fill('input[name="vehicle_make"]', 'Ford');
    await page.fill('input[name="vehicle_model"]', 'F-550');
    await page.fill('input[name="vehicle_vin"]', `1FDUF5HT5KED${Date.now().toString().slice(-5)}`);
    await page.fill('input[name="vehicle_unit_number"]', `TRUCK-${Date.now().toString().slice(-3)}`);
    await page.fill('input[name="vehicle_license_plate"]', `WA${Date.now().toString().slice(-4)}`);

    await page.getByRole('button', { name: 'Create Equipment' }).click();
    await expect(page.url()).toContain('/inspections/new/?equipment_id=');
  }

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login/', { waitUntil: 'domcontentloaded' });

    // Wait for form to be ready
    await page.waitForSelector('input[name="username"]', { timeout: 10000 });
    await page.waitForSelector('input[name="password"]', { timeout: 10000 });

    // Fill credentials
    await page.locator('input[name="username"]').fill('josh');
    await page.locator('input[name="password"]').fill('workAccount');

    // Submit login form
    await Promise.all([
      page.waitForNavigation({ timeout: 10000 }),
      page.getByRole('button', { name: 'Login' }).click()
    ]);

    // Verify we're on the home page
    await expect(page).toHaveURL('/');
  });

  test('02 - Create Equipment', async ({ page }) => {
    customerName = `Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // First create a customer
    await page.goto('/customers/new/');
    await page.fill('input[name="name"]', customerName);
    await page.getByRole('button', { name: 'Create Customer' }).click();
    await expect(page).toHaveURL('/equipment/new/');

    // Fill required equipment fields
    await page.selectOption('select[name="customer"]', { label: customerName });
    await page.fill('input[name="location"]', 'Test Warehouse');
    await page.fill('input[name="serial_number"]', equipmentSerial);
    await page.fill('input[name="make"]', 'TestMake');
    await page.fill('input[name="model"]', 'TestModel');

    await page.getByRole('button', { name: 'Create Equipment' }).click();

    // Should redirect to inspection creation with equipment pre-selected
    await expect(page.url()).toContain('/inspections/new/?equipment_id=');
  });

  test('03 - Create Equipment with Category', async ({ page }) => {
    equipmentSerial = `CAT${Date.now()}`;
    customerName = `Category Customer ${Date.now()}`;

    // Create customer and equipment with category
    await page.goto('/customers/new/');
    await page.fill('input[name="name"]', customerName);
    await page.getByRole('button', { name: 'Create Customer' }).click();
    await expect(page).toHaveURL('/equipment/new/');

    await page.selectOption('select[name="customer"]', { label: customerName });
    await page.fill('input[name="location"]', 'Test Location');
    await page.fill('input[name="serial_number"]', equipmentSerial);
    await page.fill('input[name="make"]', 'TestMake');

    // Select category if available
    if (await page.locator('select[name="category"]').isVisible()) {
      await page.selectOption('select[name="category"]', 'b');
    }

    await page.getByRole('button', { name: 'Create Equipment' }).click();

    // Should redirect to inspection creation
    await expect(page.url()).toContain('/inspections/new/?equipment_id=');
  });

  test('04 - View Inspection History', async ({ page }) => {
    customerName = `History Customer ${Date.now()}`;
    equipmentSerial = `HIST${Date.now()}`;

    // Setup
    await page.goto('/customers/new/');
    await page.fill('input[name="name"]', customerName);
    await page.getByRole('button', { name: 'Create Customer' }).click();
    await expect(page).toHaveURL('/equipment/new/');

    await page.selectOption('select[name="customer"]', { label: customerName });
    await page.fill('input[name="location"]', 'Test Location');
    await page.fill('input[name="serial_number"]', equipmentSerial);
    await page.getByRole('button', { name: 'Create Equipment' }).click();

    // Should redirect to inspection creation
    await expect(page.url()).toContain('/inspections/new/?equipment_id=');

    // Create an inspection - index 0 because no placeholder when equipment is pre-selected
    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.getByRole('button', { name: 'Start Inspection' }).click();

    // Should be on inspection detail page
    await expect(page.url()).toContain('/inspections/');
  });

  test('05 - Generate PDF Package with All Passing Answers', async ({ page }) => {
    test.setTimeout(120000); // Extend timeout to 2 minutes for this long test
    customerName = `Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // Setup: Create customer and equipment with full details
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial, 'Terex Hi-Ranger');

    // Create inspection
    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.getByRole('button', { name: 'Start Inspection' }).click();

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Answer all 44 questions as PASS
    let questionsAnswered = 0;
    while (questionsAnswered < 44) {
      // Wait for page to be ready
      await page.waitForLoadState('networkidle');

      // Check if there are any unanswered questions (look for radio buttons that aren't checked)
      const unansweredQuestions = await page.locator('input[type="radio"][name="status"]:not(:checked)').count();
      if (unansweredQuestions === 0) break;

      // Find the first question that hasn't been answered
      const firstUnansweredPass = page.locator('input[type="radio"][value="pass"]:not(:checked)').first();
      const questionId = await firstUnansweredPass.getAttribute('data-question-id');

      // Click Pass label for this question
      await page.locator(`label[for="pass-${questionId}"]`).click();
      await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered + 1} - All checks passed`);
      await page.locator(`#question-${questionId} button:has-text("Save Answer")`).click();

      // Wait for the answer to be saved and page to reload
      await page.waitForTimeout(500);
      questionsAnswered++;
    }

    // Complete the inspection - first scroll to top and expand Inspection Information section
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    // Click to expand the Inspection Information details if collapsed
    const inspectionInfoSummary = page.locator('summary:has-text("Inspection Information")');
    if (await inspectionInfoSummary.isVisible()) {
      await inspectionInfoSummary.click();
      await page.waitForTimeout(300);
    }

    await page.locator('a:has-text("Complete Inspection")').click();

    // Click the confirmation button to finalize and generate PDFs
    await page.waitForTimeout(500);
    await page.locator('button:has-text("Confirm & Complete")').click();

    // Wait for completion and PDF generation (this takes a few seconds)
    await page.waitForTimeout(5000);

    // Verify PDF Package download link is present
    const packageLink = page.locator('a:has-text("Download Package PDF")');
    await expect(packageLink).toBeVisible();

    // Download the PDF package
    const downloadPromise = page.waitForEvent('download');
    await packageLink.click();
    const download = await downloadPromise;

    // Verify download has .pdf extension
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('06 - Generate PDF Package with One Failed Answer', async ({ page }) => {
    test.setTimeout(120000); // Extend timeout to 2 minutes for this long test
    customerName = `Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // Setup: Create customer and equipment with full details
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial, 'Altec AT40G');

    // Create inspection
    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.getByRole('button', { name: 'Start Inspection' }).click();

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Answer first 43 questions as PASS, last question as FAIL with defect
    let questionsAnswered = 0;
    while (questionsAnswered < 44) {
      // Wait for page to be ready
      await page.waitForLoadState('networkidle');

      // Check if there are any unanswered questions (look for radio buttons that aren't checked)
      const unansweredQuestions = await page.locator('input[type="radio"][name="status"]:not(:checked)').count();
      if (unansweredQuestions === 0) break;

      // Find the first question that hasn't been answered
      const firstUnansweredPass = page.locator('input[type="radio"][value="pass"]:not(:checked)').first();
      const questionId = await firstUnansweredPass.getAttribute('data-question-id');

      if (questionsAnswered < 43) {
        // Click Pass for first 43 questions
        await page.locator(`label[for="pass-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered + 1} - All checks passed`);
      } else {
        // Click Fail for the last question (44th)
        await page.locator(`label[for="fail-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill('Question 44 - Critical failure detected');

        // Fill defect details
        await page.locator(`#question-${questionId} textarea[name="defect_note"]`).fill('Structural damage found - requires immediate repair');

        // Create a simple test image file for upload
        const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');

        // Upload defect photo
        const fileInput = await page.locator(`#question-${questionId} input[type="file"]`);
        await fileInput.setInputFiles({
          name: 'defect.png',
          mimeType: 'image/png',
          buffer: buffer
        });
      }

      // Wait for navigation after clicking Save Answer
      await Promise.all([
        page.waitForNavigation(),
        page.locator(`#question-${questionId} button:has-text("Save Answer")`).click()
      ]);

      // Wait a bit for page to be ready
      await page.waitForTimeout(300);
      questionsAnswered++;
    }

    // Complete the inspection - first scroll to top and expand Inspection Information section
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    // Click to expand the Inspection Information details if collapsed
    const inspectionInfoSummary = page.locator('summary:has-text("Inspection Information")');
    if (await inspectionInfoSummary.isVisible()) {
      await inspectionInfoSummary.click();
      await page.waitForTimeout(300);
    }

    await page.locator('a:has-text("Complete Inspection")').click();

    // Click the confirmation button to finalize and generate PDFs
    await page.waitForTimeout(500);
    await page.locator('button:has-text("Confirm & Complete")').click();

    // Wait for completion and PDF generation (this takes a few seconds)
    await page.waitForTimeout(5000);

    // Verify PDF Package download link is present
    const packageLink = page.locator('a:has-text("Download Package PDF")');
    await expect(packageLink).toBeVisible();

    // Download the PDF package
    const downloadPromise = page.waitForEvent('download');
    await packageLink.click();
    const download = await downloadPromise;

    // Verify download has .pdf extension
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('07 - Generate PDF Package with Multiple Failures', async ({ page }) => {
    test.setTimeout(120000);
    customerName = `Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // Setup: Create customer and equipment with full details
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial, 'Versalift VST-240');

    // Create inspection
    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.getByRole('button', { name: 'Start Inspection' }).click();
    await page.waitForLoadState('networkidle');

    // Answer questions: PASS for most, FAIL for questions 5, 15, and 30
    const failQuestions = [5, 15, 30];
    let questionsAnswered = 0;
    let maxIterations = 50; // Safety limit to prevent infinite loops

    while (questionsAnswered < maxIterations) {
      await page.waitForLoadState('networkidle');

      // Check if there are any unanswered questions
      const unansweredCount = await page.locator('input[type="radio"][value="pass"]:not(:checked)').count();

      // Debug: Log count of unanswered questions
      console.log(`[Test 11] Iteration ${questionsAnswered + 1}: Found ${unansweredCount} unanswered Pass buttons`);

      if (unansweredCount === 0) {
        console.log(`[Test 11] Breaking at iteration ${questionsAnswered + 1}: All questions answered`);
        break;
      }

      const firstUnansweredPass = page.locator('input[type="radio"][value="pass"]:not(:checked)').first();
      const questionId = await firstUnansweredPass.getAttribute('data-question-id');

      // Debug: Log question ID
      console.log(`[Test 11] Iteration ${questionsAnswered + 1}: Answering question ID ${questionId}`);

      questionsAnswered++;

      if (failQuestions.includes(questionsAnswered)) {
        // Fail this question with defect
        await page.locator(`label[for="fail-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered} - Failed inspection`);
        await page.locator(`#question-${questionId} textarea[name="defect_note"]`).fill(`Defect found on question ${questionsAnswered} - needs attention`);

        const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
        const fileInput = await page.locator(`#question-${questionId} input[type="file"]`);
        await fileInput.setInputFiles({
          name: `defect-q${questionsAnswered}.png`,
          mimeType: 'image/png',
          buffer: buffer
        });
      } else {
        await page.locator(`label[for="pass-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered} - Pass`);
      }

      await page.locator(`#question-${questionId} button:has-text("Save Answer")`).click();
      await page.waitForTimeout(500);
    }

    // Complete inspection
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    const inspectionInfoSummary = page.locator('summary:has-text("Inspection Information")');
    if (await inspectionInfoSummary.isVisible()) {
      await inspectionInfoSummary.click();
      await page.waitForTimeout(300);
    }
    await page.locator('a:has-text("Complete Inspection")').click();
    await page.waitForTimeout(500);
    await page.locator('button:has-text("Confirm & Complete")').click();
    await page.waitForTimeout(5000);

    const packageLink = page.locator('a:has-text("Download Package PDF")');
    await expect(packageLink).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await packageLink.click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('08 - Generate PDF Package with Measurement Failure', async ({ page }) => {
    test.setTimeout(120000);
    customerName = `Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // Setup: Create customer and equipment with full details
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial, 'Terex TL38P');

    // Create inspection
    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.getByRole('button', { name: 'Start Inspection' }).click();
    await page.waitForLoadState('networkidle');

    // Answer all questions as PASS, but fail one with measurement value
    let questionsAnswered = 0;
    let measurementQuestionFound = false;

    while (questionsAnswered < 44) {
      await page.waitForLoadState('networkidle');
      const unansweredQuestions = await page.locator('input[type="radio"][name="status"]:not(:checked)').count();
      if (unansweredQuestions === 0) break;

      const firstUnansweredPass = page.locator('input[type="radio"][value="pass"]:not(:checked)').first();
      const questionId = await firstUnansweredPass.getAttribute('data-question-id');

      // Check if this question has a measurement field
      const measurementField = page.locator(`#question-${questionId} input[name="measurement_value"]`);
      const hasMeasurement = await measurementField.count() > 0;

      if (hasMeasurement && !measurementQuestionFound && questionsAnswered > 5) {
        // First measurement question after #5 - fail it with out-of-spec measurement
        measurementQuestionFound = true;
        await page.locator(`label[for="fail-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered + 1} - Measurement out of specification`);

        // Fill measurement with failing value
        await measurementField.fill('125.5');

        // Add defect details
        await page.locator(`#question-${questionId} textarea[name="defect_note"]`).fill('Measurement exceeds acceptable range - requires calibration or replacement');

        const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
        const fileInput = await page.locator(`#question-${questionId} input[type="file"]`);
        await fileInput.setInputFiles({
          name: 'measurement-defect.png',
          mimeType: 'image/png',
          buffer: buffer
        });
      } else {
        // Pass this question
        await page.locator(`label[for="pass-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered + 1} - Pass`);

        // If it has measurement, fill with passing value
        if (hasMeasurement) {
          await measurementField.fill('50.0');
        }
      }

      await Promise.all([
        page.waitForNavigation(),
        page.locator(`#question-${questionId} button:has-text("Save Answer")`).click()
      ]);

      await page.waitForTimeout(300);
      questionsAnswered++;
    }

    // Complete inspection
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    const inspectionInfoSummary = page.locator('summary:has-text("Inspection Information")');
    if (await inspectionInfoSummary.isVisible()) {
      await inspectionInfoSummary.click();
      await page.waitForTimeout(300);
    }
    await page.locator('a:has-text("Complete Inspection")').click();
    await page.waitForTimeout(500);
    await page.locator('button:has-text("Confirm & Complete")').click();
    await page.waitForTimeout(5000);

    const packageLink = page.locator('a:has-text("Download Package PDF")');
    await expect(packageLink).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await packageLink.click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('09 - Generate PDF Package with Mixed Results', async ({ page }) => {
    test.setTimeout(120000);
    customerName = `Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // Setup: Create customer and equipment with full details
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial, 'Elliott G85R');

    // Create inspection
    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.getByRole('button', { name: 'Start Inspection' }).click();
    await page.waitForLoadState('networkidle');

    // Mix of PASS, FAIL, and N/A
    const failQuestions = [10, 25];
    const naQuestions = [20, 35];
    let questionsAnswered = 0;
    let maxIterations = 50; // Safety limit to prevent infinite loops

    while (questionsAnswered < maxIterations) {
      await page.waitForLoadState('networkidle');

      // Check if there are any unanswered questions
      const unansweredCount = await page.locator('input[type="radio"][value="pass"]:not(:checked)').count();
      if (unansweredCount === 0) {
        console.log(`[Test 13] All questions answered after ${questionsAnswered} iterations`);
        break;
      }

      const firstUnansweredPass = page.locator('input[type="radio"][value="pass"]:not(:checked)').first();
      const questionId = await firstUnansweredPass.getAttribute('data-question-id');
      questionsAnswered++;

      if (failQuestions.includes(questionsAnswered)) {
        await page.locator(`label[for="fail-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered} - Failed`);
        await page.locator(`#question-${questionId} textarea[name="defect_note"]`).fill(`Issue identified requiring repair`);

        const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
        const fileInput = await page.locator(`#question-${questionId} input[type="file"]`);
        await fileInput.setInputFiles({
          name: `defect-q${questionsAnswered}.png`,
          mimeType: 'image/png',
          buffer: buffer
        });
      } else if (naQuestions.includes(questionsAnswered)) {
        await page.locator(`label[for="na-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered} - Not applicable to this equipment`);
      } else {
        await page.locator(`label[for="pass-${questionId}"]`).click();
        await page.locator(`#question-${questionId} textarea[name="notes"]`).fill(`Question ${questionsAnswered} - Pass`);
      }

      await page.locator(`#question-${questionId} button:has-text("Save Answer")`).click();
      await page.waitForTimeout(500);
    }

    // Complete inspection
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    const inspectionInfoSummary = page.locator('summary:has-text("Inspection Information")');
    if (await inspectionInfoSummary.isVisible()) {
      await inspectionInfoSummary.click();
      await page.waitForTimeout(300);
    }
    await page.locator('a:has-text("Complete Inspection")').click();
    await page.waitForTimeout(500);
    await page.locator('button:has-text("Confirm & Complete")').click();
    await page.waitForTimeout(5000);

    const packageLink = page.locator('a:has-text("Download Package PDF")');
    await expect(packageLink).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await packageLink.click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('10 - Complete Inspection with All Test Modules (Dielectric, Load, Functional)', async ({ page }) => {
    test.setTimeout(180000);  // 3 minutes for full inspection with test modules
    customerName = `Complete Test Customer ${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    // Setup: Create customer and equipment with full details
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial, 'Terex Hi-Ranger');

    // Start inspection - verify we're on the new inspection page
    await expect(page.url()).toContain('/inspections/new/');

    // Wait for and select the dropdown (there should only be one select on this page)
    const selectElement = page.locator('select').first();
    await selectElement.waitFor({ state: 'visible', timeout: 10000 });

    // Get all options and find the one containing "Periodic"
    const options = await selectElement.locator('option').allTextContents();
    const periodicOption = options.find(opt => opt.includes('Periodic'));
    await selectElement.selectOption(periodicOption);

    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/inspections\/\d+\//);

    console.log('[Test 10] Starting complete inspection with all test modules');

    // Answer all inspection questions with PASS
    let iteration = 0;
    while (true) {
      iteration++;
      const passButtons = await page.locator('button.pass-button:not(.selected)').count();
      console.log(`[Test 10] Iteration ${iteration}: Found ${passButtons} unanswered Pass buttons`);

      if (passButtons === 0) {
        console.log(`[Test 10] Breaking at iteration ${iteration}: All questions answered`);
        break;
      }

      if (iteration > 100) {
        throw new Error(`[Test 10] Exceeded 100 iterations - possible infinite loop`);
      }

      const questionElement = page.locator('button.pass-button:not(.selected)').first();
      const questionId = await questionElement.getAttribute('data-question-id');
      console.log(`[Test 10] Iteration ${iteration}: Answering question ID ${questionId}`);

      await questionElement.click();
      await page.waitForTimeout(100);
    }

    console.log(`[Test 10] All questions answered after ${iteration} iterations`);

    // Add Dielectric Test Module
    console.log('[Test 10] Adding Dielectric Test Module');
    await page.locator('a[href*="add_test_module"]').click();
    await page.waitForURL(/\/inspections\/\d+\/add_test_module\//);

    await page.selectOption('select[name="template"]', { label: /Dielectric/i });
    await page.waitForTimeout(500);

    // Fill dielectric test data
    await page.fill('input[name="test_voltage"]', '46');
    await page.fill('input[name="leakage_current_upper"]', '3.2');
    await page.fill('input[name="leakage_current_lower"]', '2.8');
    await page.fill('input[name="leakage_current_bucket_liner"]', '1.5');
    await page.fill('input[name="leakage_current_upper_controls"]', '2.1');
    await page.fill('input[name="test_duration"]', '3');
    await page.selectOption('select[name="weather_conditions"]', 'Clear');
    await page.fill('input[name="ambient_temperature"]', '72');

    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/inspections\/\d+\//);
    console.log('[Test 10] Dielectric test added successfully');

    // Add Load Test Module
    console.log('[Test 10] Adding Load Test Module');
    await page.locator('a[href*="add_test_module"]').click();
    await page.waitForURL(/\/inspections\/\d+\/add_test_module\//);

    await page.selectOption('select[name="template"]', { label: /Load/i });
    await page.waitForTimeout(500);

    // Fill load test data
    await page.fill('input[name="rated_capacity"]', '500');
    await page.fill('input[name="test_load"]', '625');
    await page.fill('input[name="basket_load"]', '500');
    await page.fill('input[name="boom_angle"]', '45');
    await page.fill('input[name="test_duration"]', '5');

    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/inspections\/\d+\//);
    console.log('[Test 10] Load test added successfully');

    // Mark inspection as completed
    console.log('[Test 10] Marking inspection as completed');
    await page.locator('a:has-text("Mark Complete")').click();
    await page.waitForURL(/\/inspections\/\d+\/complete\//);

    await page.selectOption('select[name="overall_result"]', 'pass');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/inspections\/\d+\//);

    console.log('[Test 10] Inspection completed');

    // Generate PDF Package
    console.log('[Test 10] Generating PDF package');
    await page.locator('a:has-text("Generate PDF Package")').click();
    await page.waitForTimeout(3000);  // Wait for PDF generation

    const pdfLink = page.locator('a[href*="inspection_package"]').first();
    await expect(pdfLink).toBeVisible({ timeout: 10000 });

    console.log('[Test 10] PDF package generated successfully with all test modules!');
  });

  test('11 - Logout', async ({ page }) => {
    await page.goto('/');

    // Find and submit logout form
    await page.locator('form[action="/logout/"]').locator('button[type="submit"]').click();

    // Should redirect to login page (may or may not have ?next= parameter)
    await expect(page.url()).toContain('/login/');
  });
});
