# LAD-CAM

## Abstract
CAD engineers usually don’t get it right the first time. They keep making changes and improvements until they get it just right. This traditional way works, but it’s slow and relies on really skilled engineers. To solve these problems, we created LAD-CAM, a new way to make CAD designs. LAD-CAM uses a big language model to create CAD code. It also uses a self-refinement loop to make the CAD model even better. LAD-CAM doesn’t need any special training or data. It uses the language model to make the code and then uses feedback from another model to make it even better. We also made a dataset with all the common things CAD engineers do. We tested our framework with this dataset and found that when we used GPT-4 Turbo as the language model, the first time we tried it, it got 53.6% of the designs right. After we made some changes, the success rate went up to 76.7%. The biggest improvement came in the first round of refinement. After that, the accuracy of the correct designs didn’t get much better.

## How to run the system
1. Download and setup the [FreeCAD](https://github.com/FreeCAD/FreeCAD) software. Currently, the system has been tested on Windows and Linux OS with a screen size of 1920x1080.
2. Clone the repository.
```
git clone https://github.com/kh-ops69/LAD-CAM.git
```

3. Set up Together AI API to use Llama models or get the API key of OpenAI to use GPT models. Take a look at args in src/run.py for arguments that you can specify. Assuming the keys are already set, run the below command to run the system.
```
python src/run.py --code_gen_model codellama/chatgpt/llama3/gpt4-turbo --reasoning_model codellama/chatgpt/llama3/gpt4-turbo --human_feedback True
```

4. The results will be stored in the results/ folder and new queries can be added in data/queries.txt

## Future Improvements
We are planning to release improved versions of this utility. Following changes are planned:
1. Set up utility to utilize locally running Large Language Models(LLMs)
2. Improve code generation process
3. Improve recognition of key points in user query and generate additional information to assist in code generation process. 
