from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

# Initialize the WebDriver and install ChromeDriver if necessary
def start_explorer():
    try:
        driver = webdriver.Chrome()
        return driver
    except WebDriverException:
        input("ChromeDriver is not installed. Press 'ENTER' to install...")
        print("Installing ChromeDriver...")
        return webdriver.Chrome(ChromeDriverManager().install())

# Helper function to select an option from a dropdown by value
def select_option(driver, id_menu, value):
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, id_menu)))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_menu)))
        menu = driver.find_element(By.ID, id_menu)
        select = Select(menu)
        select.select_by_value(value)
    except Exception as e:
        print(f"Error selecting option in menu '{id_menu}': {e}")

# Function to upload a question to the platform
def upload_question(driver, question_data, question_number):
    try:
        print(f"Uploading question {question_number}...")

        # Set difficulty level based on question number
        difficulty_level = '1' if question_number <= 5 else '2' if question_number <= 10 else '3'
        select_option(driver, 'level_id', difficulty_level)

        # Fill the question field
        question_field = driver.find_elements(By.CLASS_NAME, "note-editable")[0]
        action = ActionChains(driver)
        action.click(question_field).send_keys(question_data['question']).perform()

        # Set question type based on number of correct answers
        question_type = '3' if len(question_data['correct_answer']) == 1 else '1'
        select_option(driver, 'type_id', question_type)

        # Select topic (hardcoded as '3')
        select_option(driver, 'topic_id', '3')

        # Set points for the question (always 10)
        points_field = driver.find_elements(By.ID, "points")[1]
        points_field.send_keys("10")

        # Select the number of answers
        answers_count = str(len(question_data['answers']))
        select_option(driver, 'cant_questions', answers_count)

        # Fill in the answers and mark the correct ones
        for i, answer in enumerate(question_data['answers'], start=1):
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.NAME, f"answer[{i}]text")))
            driver.find_element(By.NAME, f"answer[{i}]text").send_keys(answer)
            if i in question_data['correct_answer']:
                driver.find_element(By.NAME, f"is_correct[{i}]correct").click()

        # Optionally fill the explanation field
        if 'explanation' in question_data:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "explicacion")))
            driver.find_element(By.ID, "explicacion").send_keys(question_data['explanation'])

        # Set objectives (hardcoded as '1')
        driver.find_element(By.ID, "objetivos").send_keys("1")

        # Save the question
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Guardar')]")
        driver.execute_script("arguments[0].click();", save_button)

        print(f"Question {question_number} uploaded successfully.")

        # Check the box to keep the form open for the next question
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "new_question"))).click()

    except Exception as e:
        print(f"Error uploading question {question_number}: {e}")

# Function to process the questions from a text file
def process_questions(driver, exam):
    question_number = 0

    with open(f"{exam}.txt", 'r', encoding='utf-8') as file:
        question_data = {}
        answers = []
        question_data['correct_answer'] = []

        for line in file:
            line = line.strip()

            if line.startswith('Pregunta'):
                question_number += 1
                question_data = {'correct_answer': []}
                answers = []
                question_data['question'] = line.split(":", 1)[1].strip()

            elif ')' in line and len(line.split(')')[0]) == 1 and not line.startswith('Opción correcta:'):
                _, clean_answer = line.split(')', 1)
                if "(Respuesta correcta)" in clean_answer:
                    question_data['correct_answer'].append(len(answers) + 1)
                    clean_answer = clean_answer.replace("(Respuesta correcta)", "").strip()
                answers.append(clean_answer)

            elif line.startswith('Opción correcta:'):
                correct_answer_letter = line.split(':')[1].split(")")[0].lower().strip()
                correct_answer_index = 'abcdefgh'.index(correct_answer_letter) + 1
                question_data['correct_answer'].append(correct_answer_index)

            elif line.startswith('Explicación:'):
                question_data['explanation'] = line.split(':', 1)[1].strip()

            elif line.startswith('!'):
                question_data['answers'] = answers
                upload_question(driver, question_data, question_number)

# Main program flow
if __name__ == '__main__':
    url = input("Paste the URL where you need to upload the questions: ")
    exam = input("Enter the exam file name (without '.txt'): ")

    try:
        driver = start_explorer()
        driver.get(url)
        driver.maximize_window()

        # Login steps (add credentials)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys("# USER LOGIN CREDENTIALS")
        driver.find_element(By.ID, "password").send_keys("# USER LOGIN CREDENTIALS")
        driver.find_element(By.ID, "loginButton").click()

        driver.get(url)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "new_question"))).click()

        process_questions(driver, exam)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        input("All questions uploaded. Press ENTER to close the program.")
        driver.quit()
