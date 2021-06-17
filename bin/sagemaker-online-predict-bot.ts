#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { SageMakerOnlinePredictBotStack } from '../lib/sagemaker-online-predict-bot-stack';

const app = new cdk.App();
new SageMakerOnlinePredictBotStack(app, 'SageMakerOnlinePredictBotStack');
