import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError
import uuid
import json
# from API.prompt_templates import *
from prompt_templates import *

# load_dotenv()
# agent_role = os.environ.get('AGENT_ROLE')


class VctClient():
    def __init__(self,
                 region_name="us-east-1"):
        self.region_name = region_name
        self.agentId = "VMPZXQYLQ0"
        self.agentAlias = "T076UHLG01"

    def return_runtime_client(self, run_time=True) -> BaseClient:
        if run_time:
            bedrock_client = boto3.client(
                service_name="bedrock-agent-runtime",
                region_name=self.region_name)
        else:
            bedrock_client = boto3.client(
                service_name="bedrock-agent",
                region_name=self.region_name)

        return bedrock_client

    def invoke_bedrock_agent(self,
                             agent_id,
                             agent_alias_id,
                             session_id,
                             prompt=None, 
                             filters = {
                                    "andAll": [
                                        {
                                            "in": {
                                                "key": "region",
                                                "value": ["amer", "emea","cn","ap"]
                                            }
                                        },
                                        {
                                            "in": {
                                                "key": "league",
                                                "value": ["international", "challengers", "gc"]
                                            }
                                        }
                                    ]
                                }):

        completion = ""
        traces =[]
        try:
            bedrock_client = self.return_runtime_client(run_time=True)
            response = bedrock_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=prompt,
                sessionState={
                    'knowledgeBaseConfigurations': [
                        {
                            'knowledgeBaseId': 'MMUTW03GYI',
                            'retrievalConfiguration': {
                                'vectorSearchConfiguration': {
                                    "filter": filters,
                                    'numberOfResults': 40,
                                }
                            }
                        },
                    ]
                }
            )
            for event in response.get("completion"):
                try:
                    trace = event["trace"]
                    traces.append(trace['trace'])
                except KeyError:
                    chunk = event["chunk"]
                    completion = completion + chunk["bytes"].decode()
                except Exception as e:
                    print(e)

        except ClientError as e:
            print(e)

        return completion
    
    def categorize_input(self, input):
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        # Set the model ID, e.g., Claude 3 Haiku.
        model_id = "anthropic.claude-instant-v1"
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": input + CATEGORIZE_TEMPLATE_STR}],
                }
            ],
        }
        request = json.dumps(native_request)
        response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        return response_text
    def get_filters(self, input):
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        # Set the model ID, e.g., Claude 3 Haiku.
        model_id = "anthropic.claude-instant-v1"
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": GET_FILTERS_TEMPLATE_STR + input}],
                }
            ],
        }
        request = json.dumps(native_request)
        response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        return response_text

    def create_team(self, input, uuid):
        model_id = "anthropic.claude-instant-v1"
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        filters = json.loads(self.get_filters(input))
        player_list = bedrock_client.invoke_bedrock_agent(agent_id=bedrock_client.agentId,
                                                    agent_alias_id=bedrock_client.agentAlias,
                                                   session_id=uuid,
                                                   prompt = GATHER_TEAM_TEMPLATE_STR,
                                                   filters=filters)
        player_array = player_list.split(', ')
        player_array.append('meta')
        filtered_players = {
                    "in": {
                            "key": "player",
                            "value": player_array
                        }
                }
        response = bedrock_client.invoke_bedrock_agent(agent_id=bedrock_client.agentId,
                                                        agent_alias_id=bedrock_client.agentAlias,
                                                        session_id=uuid + "2",
                                                        prompt = CREATE_TEAM_TEMPLATE_STR + input,
                                                        filters=filtered_players)



        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": PARSE_CREATE_TEAM_TEMPLATE_STR + response}],
                }
            ],
        }
        request = json.dumps(native_request)
        adjusted_response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(adjusted_response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        return response_text
    
    def edit_team(self, input, current_team, uuid):
        model_id = "anthropic.claude-instant-v1"
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        print(self.describe_team(current_team) + input + EDIT_TEAM_TEMPLATE_STR)
        raw = self.invoke_bedrock_agent(agent_id=self.agentId,
                                                agent_alias_id=self.agentAlias,
                                                session_id= uuid,
                                                prompt = self.describe_team(current_team) + input + EDIT_TEAM_TEMPLATE_STR)
        print(raw)
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": PARSE_EDIT_TEAM_TEMPLATE_STR + raw}],
                }
            ],
        }
        request = json.dumps(native_request)
        adjusted_response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(adjusted_response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        return response_text
    def search_kb(self, input, uuid):
        model_id = "anthropic.claude-instant-v1"
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        raw = self.invoke_bedrock_agent(agent_id=self.agentId,
                                                    agent_alias_id=self.agentAlias,
                                                    session_id=uuid,
                                                    prompt = input)

        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": OUTPUT_CLEANER_TEMPLATE_STR + raw}],
                }
            ],
        }
        request = json.dumps(native_request)
        adjusted_response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(adjusted_response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        return response_text
    def analyze_team(self, input, current_team, uuid):
        model_id = "anthropic.claude-instant-v1"
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        raw = self.invoke_bedrock_agent(agent_id=self.agentId,
                                                    agent_alias_id=self.agentAlias,
                                                    session_id=uuid,
                                                    prompt = self.describe_team(current_team) + input)

        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": OUTPUT_CLEANER_TEMPLATE_STR + raw}],
                }
            ],
        }
        request = json.dumps(native_request)
        adjusted_response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(adjusted_response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        return response_text
        
    def describe_team(self, team):
        num_empty_slots = 5 - len(team)
    
        team_description = ', '.join(team)
        
        # Construct the output string based on empty slots
        if num_empty_slots > 0:
            return f"Given the team of Valorant professional players, {team_description}, with {num_empty_slots} empty slot(s),"
        else:
            return f"Given the team of Valorant professional players, {team_description}, "
if __name__ == "__main__":
    bedrock_client = VctClient()
    # bedrock_runtime_client = bedrock_client.return_runtime_client()

    # agents = bedrock_client.list_agents()
    # print(agents)
    jing = str(uuid.uuid4())
    request = "Build a team using only players from VCT International. Assign roles to each player and explain why this composition would be effective in a competitive match."
    print(bedrock_client.create_team(request, jing))
    # print(bedrock_client.create_team(request,jing ))




    # response = bedrock_client.invoke_bedrock_agent(agent_id="VMPZXQYLQ0",
    #                                                agent_alias_id="T076UHLG01",
    #                                                session_id="1234",
    #                                                prompt = PARSE_TEAM_TEMPLATE_STR + response)
    # for x in create_team_prompts:
    #     print(x)
    #     response = bedrock_client.categorize_input(x)
    #     print(response)

    # for x in edit_team_prompts:
    #     print(x)
    #     response = bedrock_client.categorize_input(x)
    #     print(response)
    # for x in valorant_news_stats_prompts:
    #     print(x)
    #     response = bedrock_client.categorize_input(x)
    #     print(response)
    # for x in other_prompts:
    #     print(x)
    #     response = bedrock_client.categorize_input(x)
        
        
