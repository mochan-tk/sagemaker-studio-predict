import os
import json
import boto3

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, PostbackEvent, PostbackAction, QuickReply, QuickReplyButton
)

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

channel_secret = '<your secret key>'
channel_access_token = '<your access token>'

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

def handler(event, context):
    signature = event["headers"]["x-line-signature"]
    body = event["body"]
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}
    error_json = {"isBase64Encoded": False,
                  "statusCode": 403,
                  "headers": {},
                  "body": "Error"}

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        logger.error("Got exception from LINE Messaging API")

    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
    table_name = "sagemaker-online-predict-bot"
    dynamotable = dynamodb.Table(table_name)
    
    
    # if event is MessageEvent and message is TextMessage, then echo text #
    for event in events:
        logger.info(str(event))
        
        primary_key = {"UserId": event.source.user_id}
        if isinstance(event, PostbackEvent):
            
            res = dynamotable.get_item(Key=primary_key)
            question = str(res['Item']['Question'])
            logger.info(question)
            if question == "0":
                response = dynamotable.update_item(
                    Key=primary_key,
                    UpdateExpression="set Question = :Question, Pclass = :Pclass",
                    ExpressionAttributeValues={
                        ':Question': 1,
                        ':Pclass': event.postback.data
                })
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="年齢はいくつですか？")) 
                    
                
                
        
            elif question == "4":
                male = 0
                female = 0
                if event.postback.data == "male":
                    male = 1
                else:
                    female = 1
                    
                response = dynamotable.update_item(
                    Key=primary_key,
                    UpdateExpression="set Question = :Question, Sex_male = :Sex_male, Sex_female = :Sex_female",
                    ExpressionAttributeValues={
                        ':Question': 5,
                        ':Sex_male': male,
                        ':Sex_female': female,
                })
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='乗船した港はどれですか？',
                        quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label="Cherbourg", data="C", display_text="Cherbourg")
                                ),
                                QuickReplyButton(
                                    action=PostbackAction(label="Queenstown", data="Q", display_text="Queenstown")
                                ),
                                QuickReplyButton(
                                    action=PostbackAction(label="Southampton", data="S", display_text="Southampton")
                                )
                            ])))  
                    
            elif question == "5":
                embarked_S = 0
                embarked_C = 0
                embarked_Q = 0
                
                if event.postback.data == 'S':
                    embarked_S = 1
                elif event.postback.data == 'C':
                    embarked_C = 1
                else:
                    embarked_Q = 1
                    
                response = dynamotable.update_item(
                    Key=primary_key,
                    UpdateExpression="set Question = :Question, Embarked_S = :Embarked_S, Embarked_C = :Embarked_C, Embarked_Q = :Embarked_Q",
                    ExpressionAttributeValues={
                        ':Question': 5,
                        ':Embarked_S': embarked_S,
                        ':Embarked_C': embarked_C,
                        ':Embarked_Q': embarked_Q
                })
                
                primary_key = {"UserId": event.source.user_id}
                
                ENDPOINT_NAME = "xx-xx-staging"
                # ENDPOINT_NAME = "xx-xx-prod"
                client = boto3.client("sagemaker-runtime", region_name="ap-northeast-1")
                
                # https://www.magata.net/memo/index.php?%B7%B1%CE%FD%BA%D1%A4%DF%A5%E2%A5%C7%A5%EB%A4%F2SageMaker%A5%A8%A5%F3%A5%C9%A5%DD%A5%A4%A5%F3%A5%C8%A4%CB%A5%C7%A5%D7%A5%ED%A5%A4%A4%B9%A4%EB
                input_data = [[res['Item']['Pclass'],
                               res['Item']['Age'],
                               res['Item']['SibSp'],
                               res['Item']['Parch'],
                               res['Item']['Sex_male'],
                               res['Item']['Sex_female'],
                               embarked_S,
                               embarked_C,
                               embarked_Q]] # pclass age slibp parch male, female, S, C, Q
                # request_body = json.dumps(input_data)
                # content_type = "application/json"
                # accept_type  = "application/json"
                request_body = '\n'.join([','.join([str(x) for x in rec]) for rec in input_data])
                content_type = "text/csv"
                accept_type  = "application/json"
                
                
                # sagemakerのエンドポイントにアクセスし予測結果を受け取る
                response = client.invoke_endpoint(
                    EndpointName=ENDPOINT_NAME,
                    Body=request_body,
                    ContentType=content_type,
                    Accept=accept_type
                )
            
                response_dict = json.loads(response['Body'].read().decode("utf-8"))
                response_val = json.dumps(response_dict, indent=4)
                print(response_val)
        
                # res = dynamotable.get_item(Key={'UserId': event.source.user_id})
                # logger.info(res['Item']['Age'])
                # logger.info(type(res['Item']['Age']))
                
                if float(response_val) > 0.5:
                    line_bot_api.reply_message(
                        event.reply_token,
                        [TextSendMessage(
                            text='安心してください。あなたは無事に帰ってこれるでしょう。'),
                         StickerSendMessage(
                            package_id='11537',
                            sticker_id='52002735')]) 
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        [TextSendMessage(
                            text='あなたには困難な運命が待ち受けている...かもしれません...'),
                         StickerSendMessage(
                            package_id='11537',
                            sticker_id='52002755')]) 

            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='『予測』とメッセージを送ってみてください。'))
            
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            if '予測' == event.message.text:
                response = dynamotable.put_item(
                   Item={
                        'UserId': event.source.user_id,
                        'Question': '0'
                    }
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='チケットのクラスはどれですか？',
                        quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label="1st", data="1", display_text="1st")
                                ),
                                QuickReplyButton(
                                    action=PostbackAction(label="2nd", data="2", display_text="2nd")
                                ),
                                QuickReplyButton(
                                    action=PostbackAction(label="3rd", data="3", display_text="3rd")
                                )
                            ]))) 
                            
            
            
                
            else:
                res = dynamotable.get_item(Key={'UserId': event.source.user_id})
                question = str(res['Item']['Question'])
                logger.info(question)
                if question == "1":
                    response = dynamotable.update_item(
                            Key=primary_key,
                            UpdateExpression="set Question = :Question, Age = :Age",
                            ExpressionAttributeValues={
                                ':Question': 2,
                                ':Age': event.message.text
                        })
                    
                    line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='乗船している兄弟・配偶者の人数を教えてください。')) 
                    
                elif question == "2":
                    response = dynamotable.update_item(
                            Key=primary_key,
                            UpdateExpression="set Question = :Question, SibSp = :SibSp",
                            ExpressionAttributeValues={
                                ':Question': 3,
                                ':SibSp': event.message.text
                        })
                    
                    line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='乗船している両親・子供の人数を教えてください。')) 
                    
                elif question == "3":
                    response = dynamotable.update_item(
                            Key=primary_key,
                            UpdateExpression="set Question = :Question, Parch = :Parch",
                            ExpressionAttributeValues={
                                ':Question': 4,
                                ':Parch': event.message.text
                        })
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text='性別はどちらですか？',
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label="男性", data="male", display_text="男性")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="女性", data="female", display_text="女性")
                                    )
                                ])))
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='『予測』とメッセージを送ってみてください。'))
                    
    return 'OK'