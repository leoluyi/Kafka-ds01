#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from confluent_kafka import Producer
import sys
from datetime import datetime


# 用來接收從Consumer instance發出的error訊息
def error_cb(err):
    print(f'Error: {err}')


# 主程式進入點
if __name__ == '__main__':
    # 步驟1. 設定要連線到Kafka集群的相關設定
    props = {
        # Kafka集群在那裡?
        'bootstrap.servers': 'localhost:9092',    # <-- 置換成要連接的Kafka集群
        'error_cb': error_cb                            # 設定接收error訊息的callback函數
    }
    # 步驟2. 產生一個Kafka的Producer的實例
    producer = Producer(**props)
    # 步驟3. 指定想要發佈訊息的topic名稱
    topicName = 'test3'
    msgCounter = 0
    try:
        # produce(topic, [value], [key], [partition], [on_delivery], [timestamp], [headers])
        producer.produce(topicName, f'{datetime.now()}: Hello')
        producer.produce(topicName, f'{datetime.now()}: Hello2')
        producer.produce(topicName, f'{datetime.now()}: Hello3', 'ds0015')  # 設定 key
        producer.produce(topicName, f'{datetime.now()}: Hello4', 'ds0015')  # 設定 key

        producer.poll(0)  # 呼叫poll來讓client程式去檢查內部的Buffer, 並觸發callback
        msgCounter += 4
        print(f'Send {str(msgCounter)} messages to Kafka')
    except BufferError as e:
        # 錯誤處理
        sys.stderr.write(f'%% Local producer queue is full ({len(producer)} messages awaiting delivery): try again\n')
    except Exception as e:
        print(e)
    # 步驟5. 確認所在Buffer的訊息都己經送出去給Kafka了
    producer.flush()