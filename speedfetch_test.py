"""SpeedFetch 24/7 Ticket Scraper - Continuous Runner"""
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import os
from datetime import datetime
import warnings
import pathlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tracemalloc
import time
import sys
import traceback

# Start memory tracking
tracemalloc.start()

# Enhanced logging setup for 24/7 operation
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('speedfetch_24_7.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

test_sender_email = "vickyvora99@gmail.com"  # Your Gmail address
test_receiver_email = "vickyvora99@gmail.com"  # You can send it to yourself for testing
test_app_password = "xgwy yzam yhqi ihdx"  # 16-char Gmail App Password (not your Gmail login)


def send_email_gmail(subject, body, sender_email, receiver_email, app_password):
    try:
        # Create the message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to Gmail SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure connection
            server.login(sender_email, app_password)
            server.send_message(message)

        print("📨 Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# async def adding_tickets_to_basket(page):
async def adding_tickets_to_basket(page, smtp_user, smtp_password, receiver_email):
    try:
        await page.locator("xpath=(//a[contains(text(),'Match Tickets')])[2]").click()
        try:
            await page.wait_for_selector('//*[@class="pager__link--arrow-next"]')
        except:
            pass
        while True:
            # Re-fetch li elements after each iteration
            start_index = 0
            li_elements = await page.query_selector_all('xpath=//*[@data-id="event-list"]/li')

            # new code:
            total = len(li_elements)
            print(f"🔍 Found {total} li elements on this page.")

            while start_index < total:
                li_elements = await page.query_selector_all('xpath=//*[@data-id="event-list"]/li')  # Refresh list in case DOM changes
                li = li_elements[start_index]

                # Skip if h4 contains "Open To"
                has_open_to = await li.query_selector('xpath=.//h4[contains(text(), "Open to")]')
                if has_open_to:
                    start_index += 1
                    continue

                ticket_button = await li.query_selector('xpath=.//*[@data-qa-id="find-event-tickets-button"]')
                if ticket_button:
                    print(f"✅ Valid event found at index: {start_index}")
                    await ticket_button.click()
                    await asyncio.sleep(1.5)

                    # Click view available sections
                    await page.wait_for_selector('//*[@data-test-id="listShowButton"]', timeout=120000)
                    await page.locator("xpath=//*[@data-test-id='listShowButton']").click()

                    # Select first available seat
                    await page.wait_for_selector('xpath=//*[@data-test-id="rightRailListItems"]', timeout=120000)
                    await page.locator('xpath=//*[@data-test-id="rightRailListItems"]').first.click()

                    # Wait for the first matching element and click it
                    first_button = page.locator('xpath=//div[@data-test-id="obstractedViewIcon"]/../..').first
                    await first_button.wait_for(state="visible", timeout=120000)
                    await first_button.click()

                    # Click add to basket
                    await page.wait_for_selector('//*[@data-test-id="addToCartButtonOnDetailModal"]', timeout=120000)
                    await page.locator('xpath=//*[@data-test-id="addToCartButtonOnDetailModal"]').click()

                    event_title = await page.locator('xpath=//*[@class="eventinfo__name"]').inner_text()
                    event_date = await page.locator('xpath=//*[@class="eventinfo__date"]').inner_text()
                    send_email_gmail(
                        subject="🎟️ Ticket Added to Basket",
                        body=f"A new ticket was added to the basket.\nEvent: {event_title}\nTime: {event_date}",
                        sender_email=smtp_user,
                        receiver_email=receiver_email,
                        app_password=smtp_password
                    )

                    # Set index for next loop
                    # start_index = i + 1
                    await asyncio.sleep(10)
                    # await page.goto("https://www.eticketing.co.uk/tottenhamhotspur/Events")
                    await page.go_back()
                    await page.go_back()
                    await page.wait_for_selector('xpath=//*[@data-id="event-list"]/li')
                    # After reload, re-collect li elements and reset loop
                    li_elements = await page.query_selector_all('xpath=//*[@data-id="event-list"]/li')
                    total = len(li_elements)
                    start_index += 1
                    continue  # st
                else:
                    print(f"❌ Ticket no longer on sale at index: {start_index}")
                    start_index += 1

            # ✅ All li elements processed on current page. Try next
            next_button = page.locator('xpath=//*[@class="pager__link--arrow-next"]')

            if await next_button.is_visible() and await next_button.is_enabled():
                print("➡️ Moving to next page...")
                await next_button.click()
                await page.wait_for_selector('xpath=//*[@data-id="event-list"]/li')
                # start_index = 0  # Reset for new page
            else:
                print("🚫 Last page reached or next button is not clickable. Exiting.")
                break
    except Exception as e:
        print(f"⚠️ Exception occurred: {e}")


async def main():
    today = datetime.now().strftime('%Y-%m-%d')
    cwd = os.getcwd()
    # folder = pathlib.Path(cwd + "\\gem\\output")
    input_file = os.path.join(cwd, "speedfetch_credentials.csv")
    current_utc_time = datetime.utcnow()
    formatted_time = current_utc_time.strftime("%Y%m%d%H%M%S")
    df_credentials = pd.read_csv(input_file, encoding='utf-8')
    input_email = df_credentials['Email'].iloc[0]
    input_password = df_credentials['Password'].iloc[0]
    input_title = df_credentials['Title'].iloc[0]
    input_gender = df_credentials['Gender'].iloc[0]
    input_first_name = df_credentials['First Name'].iloc[0]
    input_surname = df_credentials['Surname'].iloc[0]
    input_dob = df_credentials['DOB'].iloc[0]
    input_address = df_credentials['Address Line 1'].iloc[0]
    input_town = df_credentials['Town'].iloc[0]
    input_county = df_credentials['County'].iloc[0]
    input_postcode = df_credentials['PostCode'].iloc[0]
    input_country = df_credentials['Country'].iloc[0]
    input_mobile = df_credentials['Mobile No.'].iloc[0]

    smtp_user = test_sender_email
    smtp_password = test_app_password
    receiver_email = test_receiver_email

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        # await context.clear_cookies()
        page = await context.new_page()
        await page.goto('https://www.eticketing.co.uk/tottenhamhotspur')
        await asyncio.sleep(1)
        await page.wait_for_selector("//*[contains(text(),'Buy Now')]", timeout=120000)

        # checking if the user is logged in or not
        try:
            await page.wait_for_selector('(//a[@data-toggle-id="myaccount"])[2]')
            print('Already logged in user !!!')
            # await adding_tickets_to_basket(page)
            await adding_tickets_to_basket(page, smtp_user, smtp_password, receiver_email)
        except:
            # if user is not logged in then do the below steps
            print('User not logged in....sign in process is underway')
            await page.wait_for_selector("(//a[contains(@href,'Authentication/Login')])[2]")
            log_in_button = await page.query_selector("(//a[contains(@href,'Authentication/Login')])[2]")
            await log_in_button.click()

            # waiting for the cookie pop-up and clicking it
            try:
                await page.wait_for_selector("//button[contains(text(),'Accept All Cookies')]")
                cookie_button = await page.query_selector("//button[contains(text(),'Accept All Cookies')]")
                await cookie_button.click()
            except:
                pass

            # if sign in registered successfully then proceed with this block otherwise go to the except block
            await page.locator('xpath=//*[@id="email"]').fill(input_email)
            await page.locator('xpath=//*[@id="password"]').fill(input_password)
            await page.locator('xpath=//*[@id="submitButton"]').click()
            await page.wait_for_timeout(3000)  # optional, adjust based on page speed

            # Try to locate the "Login failed" label
            error_label = await page.query_selector('//label[contains(text(),"Login failed")]')
            if error_label:
                print("❌ Login failed. Need to register the user on the website")
                await page.locator('xpath=//*[@id="registerButton"]').click()
                await page.wait_for_selector('//*[@id="submitButton"]')
                await page.locator('xpath=//*[@id="email"]').fill(input_email)
                await page.locator('xpath=//*[@id="confirmEmail"]').fill(input_email)
                await page.locator('xpath=//*[@id="password"]').fill(input_password)
                await page.locator('xpath=//*[@id="confirmPassword"]').fill(input_password)
                await page.select_option('#title', label=input_title)
                await page.select_option('#gender', label=input_gender)
                await page.locator('xpath=//*[@id="firstName"]').fill(input_first_name)
                await page.locator('xpath=//*[@id="lastName"]').fill(input_surname)
                await page.locator('xpath=//*[@id="day"]').fill(input_dob.split('/')[0])
                await page.locator('xpath=//*[@id="month"]').fill(input_dob.split('/')[1])
                await page.locator('xpath=//*[@id="year"]').fill(input_dob.split('/')[2])
                await page.locator('xpath=//*[@id="addressLine1"]').fill(input_address)
                await page.locator('xpath=//*[@id="town"]').fill(input_town)
                await page.locator('xpath=//*[@id="county"]').fill(input_county)
                await page.locator('xpath=//*[@id="postalCode"]').fill(input_postcode)
                await page.select_option('#country', label=input_country)
                await page.locator('xpath=//*[@id="phoneNumber"]').fill(input_mobile)
                await page.locator('xpath=//*[@id="submitButton"]').click()
                print("✅ User registered.")
                await page.wait_for_selector("//*[contains(text(),'Buy Now')]", timeout=12000)
                await adding_tickets_to_basket(page, smtp_user, smtp_password, receiver_email)

            else:
                print("✅ Login successful.")
                await page.wait_for_selector("//*[contains(text(),'Buy Now')]", timeout=12000)
                await adding_tickets_to_basket(page, smtp_user, smtp_password, receiver_email)

            pass

        await page.close()


async def continuous_runner():
    """Run the main function continuously with error handling and logging"""
    logger.info("🔄 Starting SpeedFetch 24/7 Continuous Runner")
    logger.info("📝 Logs will be saved to speedfetch_24_7.log")
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    wait_time = 300  # 5 minutes between runs
    
    while True:
        try:
            start_time = datetime.now()
            logger.info(f"🕐 Starting new iteration at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the main scraping function
            await main()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ Script completed successfully in {duration}")
            consecutive_failures = 0  # Reset failure counter
            
            logger.info(f"⏳ Waiting {wait_time} seconds before next iteration...")
            await asyncio.sleep(wait_time)
            
        except KeyboardInterrupt:
            logger.info("🛑 Received keyboard interrupt. Stopping continuous runner.")
            break
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"❌ Script failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.warning(f"🔢 Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
            
            if consecutive_failures >= max_consecutive_failures:
                logger.error(f"🚨 Too many consecutive failures ({consecutive_failures}). Stopping for safety.")
                logger.error("💡 Please check the logs and fix any issues before restarting.")
                break
            
            logger.info(f"⏳ Waiting 60 seconds before retrying...")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    logger.info("👋 Continuous runner stopped.")


if __name__ == "__main__":
    print("=" * 60)
    print("   SpeedFetch 24/7 Continuous Ticket Scraper")
    print("=" * 60)
    print()
    print("🚀 Starting continuous runner...")
    print("📝 Logs will be saved to speedfetch_24_7.log")
    print("Press Ctrl+C to stop the runner")
    print()
    
    try:
        asyncio.run(continuous_runner())
    except KeyboardInterrupt:
        print("\n🛑 Runner stopped by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("Press Enter to exit...")
    input()
