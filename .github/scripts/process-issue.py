import os
import sys
import json
from github import Github
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.utils.enums import ModelTypes
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

def get_issue_context(issue_number):
    """Extract relevant information from the issue"""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])
    issue = repo.get_issue(number=issue_number)
    print("get issue context working correctly. repo ", repo)
    return {
        "title": issue.title,
        "body": issue.body,
        "number": issue.number
    }

def generate_llm_response(context):
    """Generate response using WatsonX.ai Granite model"""
    # WatsonX.ai credentials and configuration
    api_key = os.environ.get("IBM_CLOUD_API_KEY")
    project_id = os.environ.get("IBM_PROJECT_ID")
    
    # Initialize the model
    params = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 1024,
        GenParams.MIN_NEW_TOKENS: 50,
        GenParams.TEMPERATURE: 0.7,
        GenParams.TOP_K: 50,
        GenParams.TOP_P: 0.95
    }
    
    model = Model(
        model_id=ModelTypes.FLAN_UL2,
        credentials={
            "apikey": api_key,
            "url": "https://us-south.ml.cloud.ibm.com"  # adjust region if needed
        },
        project_id=project_id,
        params=params
    )
    
    prompt = f"""You are a helpful developer assistant analyzing a GitHub issue.
    Please provide a clear and practical solution to this issue:
    
    Title: {context['title']}
    Description: {context['body']}
    
    Format your response with:
    1. Brief analysis of the issue
    2. Proposed solution with code examples if relevant
    3. Any additional considerations or alternatives
    """
    
    response = model.generate(prompt)
    return response["results"][0]["generated_text"]

def post_response(issue_number, llm_response):
    """Post LLM response back to the issue"""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])
    issue = repo.get_issue(number=issue_number)
    
    response_template = f"""
🤖 **WatsonX.ai Granite Assistant Suggested Solution**

{llm_response}

---
*This is an automated response generated by IBM WatsonX.ai Granite-34B-Code-Instruct model. A human developer will review this solution.*
    """
    
    issue.create_comment(response_template)

def main():
    # Get the event payload
    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        event = json.load(f)
    
    issue_number = event["issue"]["number"]
    
    try:
        # Process the issue
        context = get_issue_context(issue_number)
        llm_response = generate_llm_response(context)
        post_response(issue_number, llm_response)
    except Exception as e:
        print(f"Error processing issue: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()