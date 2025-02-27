import os, sys, requests, re
import pyautogui
import time
import pyperclip
import logging
from PIL import Image
from prompts import *
from llm import *

def get_queries(path):
    """
    Gets all the user queries. Assumes that they are stored in a .txt file and each new line is a new query.
    """

    with open(path, 'r', encoding='utf-8') as file:
        queries = file.readlines()

    return queries

def write_macro(code, macro_path):
    """
    Writes the generated macro in the specified path.
    """

    with open(macro_path, 'w', encoding='utf-8') as file:
        file.write(code)

def remove_backticks(text):
    """
    Post processing on generated code output -- Removes the backticks present at the end of the code
    """

    pattern = r"```"
    matches = re.finditer(pattern, text)
    position = [m.start() for m in matches] #get the location of ```
    start_position = 0

    try:
        end_position = position[0]
        code = text[start_position:end_position].strip()
    
    except:
        code = text

    return code

def gui_sequence(macro_code_path, img_path):
    """
    Runs the entire sequence -- opening FreeCAD, running generated code, capturing the isometric image,
    returning the error code if there is any.
    """
    
    pyautogui.hotkey('win') #Open Run in windows
    time.sleep(.5)
    pyautogui.typewrite('FreeCAD')  
    time.sleep(.5)
    pyautogui.press('enter')  #Enter the pyautogui
    logging.info('Opened FreeCAD software')
    time.sleep(8)
    pyautogui.hotkey('ctrl', 'o') #open the macro generated
    time.sleep(3)
    pyautogui.write(macro_code_path, interval=0.08)
    time.sleep(3)
    pyautogui.press('enter')
    logging.info('Opened the macros')
    time.sleep(1)
    #pyautogui.moveTo(622, 75)
    pyautogui.hotkey('ctrl', 'f6')#run the macro
    '''time.sleep(2)
    pyautogui.leftClick()'''
    time.sleep(2)
    
    pyautogui.hotkey('v', 'f')
    time.sleep(1)
    pyautogui.hotkey('0')#orient the CAD model in isometric view
    time.sleep(1)
    screenshot = pyautogui.screenshot(region=(543, 147, 1050, 675))
    screenshot.save(img_path)

    pyperclip.copy('') #erases whatever is copied into clipboard initially

    pyautogui.moveTo(1278, 929)
    pyautogui.leftClick()
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.hotkey('ctrl', 'c')

    error_msg = pyperclip.paste() #if no error returns an empty string.
    time.sleep(2)
    '''pyautogui.hotkey('alt', 'f4')
    time.sleep(1)
    pyautogui.press('left')
    pyautogui.press('left')
    pyautogui.press('left')
    pyautogui.press('left')
    pyautogui.press('left')
    pyautogui.press('enter') '''
    pyautogui.hotkey('ctrl', 'alt', 't')
    time.sleep(0.8)
    pyautogui.write("pkill freecad", interval=0.08)
    pyautogui.press("enter")
    pyautogui.hotkey('alt', 'f4')

    if error_msg == "":
        error_msg = None
    else:
        error_msg = error_msg

    return error_msg

def get_executable_code(gen_code, error, error_iter, model, api_key, temp, query_idx, base_url, direct_code=False, refined_code=False, refined_idx = 0):
    """
    Tries to get an executable code
    """

    updated_code = gen_code
    if direct_code:
        for i in range(1, error_iter + 1):
            error_prompt = get_error_prompt(updated_code, error)
            updated_code = get_answers(model, api_key, error_prompt, temp, base_url)
            updated_code = remove_backticks(updated_code)
            macro_path = f"results/code/query_{query_idx}_direct_attempt_{i}.FCMacro"
            write_macro(updated_code, macro_path)
            # PyAutoGUI sequence
            img_path = f"results/images/query_{query_idx}_direct_attempt_{i}.png"
            error_msg = gui_sequence(macro_path, img_path)

            if error_msg is not None:
                continue
            else:
                break

    else:
        for i in range(1, error_iter + 1):
            error_prompt = get_error_prompt(updated_code, error)
            updated_code = get_answers(model, api_key, error_prompt, temp, base_url)
            updated_code = remove_backticks(updated_code)
            macro_path = f"results/code/query_{query_idx}_refined_{refined_idx}_attempt_{i}.FCMacro"
            write_macro(updated_code, macro_path)
            # PyAutoGUI sequence
            img_path = f"results/images/query_{query_idx}_refined_{refined_idx}_attempt_{i}.png"
            error_msg = gui_sequence(macro_path, img_path)

            if error_msg is not None:
                continue
            else:
                break

    return error_msg, i, updated_code

def get_vqa_score(img_path, user_query, model):
    """
    Gets the VQA score between the generated model and user query.
    Reference: https://github.com/linzhiqiu/t2v_metrics
    """

    text = f"This image shows a CAD model of {user_query}"
    score = model(images = [img_path], texts = [text])
    return score.item()

def get_captions(img_path, processor, model, human_feedback):
    """
    Gets the caption of the image
    """

    raw_img = Image.open(img_path).convert('RGB')

    # Conditional captioning
    #text = "This image shows the CAD model of a "
    #inputs = processor(raw_img, text, return_tensors="pt").to("cuda")

    #question = "The image is a CAD model of an object. Describe the object briefly"
    inputs = processor(raw_img, return_tensors="pt").to("cuda")
    out = model.generate(**inputs)

    caption = processor.decode(out[0], skip_special_tokens = True)

    print('System generated caption: ', caption)

    if human_feedback != False:
        proceed = input("Do you want to proceed with the system generated caption? Type fp for vqa score false negative (y/n/fn): ")
  
        if proceed == 'y' or proceed == 'Y':
            caption = caption

        elif proceed == 'n' or proceed == 'N':
            caption = input("Please enter the feedback: ")

        elif proceed == 'fn' or proceed == 'FN':
            caption = proceed

    else:
        caption = caption

    return caption

def get_refined_outputs(captions, user_query, prev_code, refine_iter, model, api_key, temp, 
                        query_idx, error_iter, vqa_model, vqa_thresh, processor, caption_model, base_url, human_feedback):
    """
    Performs iterative refinement and gets the best possible output for a given user query
    """

    refined_code = prev_code
    for i in range(refine_iter):
        print('Final Caption: ', captions)
        if captions == 'fn' or captions == 'FN':
            print('Stopping the refinements as asked by user... Moving to next query')
            break

        feedback_reason_prompt = get_feedback_reason_prompt(captions, user_query, refined_code)
        refined_code = get_answers(model, api_key, feedback_reason_prompt, temp, base_url)
        refined_code = remove_backticks(refined_code)
        macro_path = f"results/code/query_{query_idx}_refined_{i}_attempt_0.FCMacro"
        write_macro(refined_code, macro_path)
        # GUI sequence
        img_path = f"results/images/query_{query_idx}_refined_{i}_attempt_0.png"
        error_msg = gui_sequence(macro_path, img_path)
        print('error_msg', error_msg)
        if error_msg is not None:
            error, success_idx, refined_code = get_executable_code(refined_code, error_msg, error_iter, model, api_key, temp, query_idx, base_url, refined_code=True, refined_idx=i)
            if error is None:
                img_path_for_captions = f"results/images/query_{query_idx}_refined_{i}_attempt_{success_idx}.png"
            else:
                print("Refinement failed... Skipping to next query")
                # TODO: Add some placeholders to return
                break

        else:
            img_path_for_captions = img_path

        # Check VQA score
        vqa_score = get_vqa_score(img_path_for_captions, user_query, vqa_model)

        if vqa_score < vqa_thresh and i != refine_iter - 1:
            print("Doing another round of refinement...")
            captions = get_captions(img_path_for_captions, processor, caption_model, human_feedback)

        elif vqa_score < vqa_thresh and i == refine_iter - 1:
            print("Could not refine enough to cross the VQA threshold that was set within the defined refinement iterations...")

        elif vqa_score >= vqa_thresh:
            print(f"Refinement was successful for query {query_idx} in refine attempt {i}...")
            break

    
