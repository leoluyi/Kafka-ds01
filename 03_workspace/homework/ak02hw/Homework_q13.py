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

from confluent_kafka import Consumer, KafkaException, KafkaError

import sys

'''
 * Tips:
 * 由於13題主要是找出unique的商品貨物編號,我們可以利用"Set"的資料容器物件來快速達成目的。
 
  * Ps. 注意!!因為Python的程式還沒有辨法自動把某一個ConsumerGroup的offst重新reset, 因此要修改成不同的ConsumerGroup ID來重新讀取topic的資料
'''

# 基本參數
KAFKA_BROKER_URL = 'localhost:9092'         # 設定要連接的Kafka群
STUDENT_ID       = 'ds0015'                 # 修改成你/妳的學員編號


# 用來接收從Consumer instance發出的error訊息
def error_cb(err):
    print('Error: %s' % err)


# 轉換msgKey或msgValue成為utf-8的字串
def try_decode_utf8(data):
    if data is not None:
        return data.decode('utf-8')
    else:
        return None

# 用來記錄是否為第一次的Rebalance事件
isFirstTime = True

# 一個callback函式, 用來重設某一個ConsumerGroup的offset值到一個Topic/Partition的最小值。方便測試與教學
def seek_to_begin(consumer, partitions):
    global isFirstTime
    # 監聽Kafka的Consumer Rebalance的event, 如果是程式跑起來的第一次
    # 我們重新對每一個partition的offset來進行重置到現在partition最小的offset值
    if isFirstTime:
        for p in partitions:
            p.offset = 0
        print('assign', partitions)
        consumer.assign(partitions)
        isFirstTime = False
        print('Reset offset to beginning')


# 主程式進入點 <---
if __name__ == '__main__':
    # 步驟1.設定要連線到Kafka集群的相關設定
    # Consumer configuration
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    props = {
        'bootstrap.servers': KAFKA_BROKER_URL,          # Kafka集群在那裡? (置換成要連接的Kafka集群)
        'group.id': STUDENT_ID,                         # ConsumerGroup的名稱 (置換成你/妳的學員ID)
        'auto.offset.reset': 'earliest',                # Offset從最前面開始
        'session.timeout.ms': 6000,
        'error_cb': error_cb                            # 設定接收error訊息的callback函數
    }

    # 步驟2. 產生一個Kafka的Consumer的實例
    consumer = Consumer(props)
    # 步驟3. 指定想要訂閱訊息的topic名稱
    topicName = 'ak02.hw.translog'
    # 步驟4. 讓Consumer向Kafka集群訂閱指定的topic
    consumer.subscribe([topicName], on_assign=seek_to_begin)  # ** Tips: 讓這支程式每次重起時都把offset移到最前面
    # 步驟5. 持續的拉取Kafka有進來的訊息
    record_counter = 0
    # 產生一個Set來保存unique的msgKey <---- 存放 "題目#13" 答案的容器
    parts_unique = set()

    try:
        while True:
            # 請求Kafka把新的訊息吐出來
            records = consumer.consume(num_messages=500, timeout=1.0)  # 批次讀取
            if records is None:
                continue

            for record in records:
                # 檢查是否有錯誤
                if record is None:
                    continue
                if record.error():
                    # 偵測是否己經讀到了partiton的最尾端
                    if record.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                         (record.topic(), record.partition(), record.offset()))
                    else:
                        # Error
                        raise KafkaException(record.error())
                else:
                    record_counter += 1
                    # ** 在這裡進行商業邏輯與訊息處理 **
                    # 取出相關的metadata
                    topic = record.topic()
                    partition = record.partition()
                    offset = record.offset()
                    timestamp = record.timestamp()
                    # 取出msgKey與msgValue
                    msgKey = try_decode_utf8(record.key())      # << 這個是商品貨物編號
                    msgValue = try_decode_utf8(record.value())  # << 這個是商品貨物交易資料
                    print(msgKey + msgValue)
                    # ** "題目#13" 的主要邏輯 **
                    # 把msgKey放進Set中 <---- 把msgKey放進 "題目#13" 答案的容器

                    # *** 你要開發的Block在這裡 [Start] ***
                    # Tips: 在Python中把值放進"Set"的collection, 使用的method是 set_object.add(商品貨物編號)

                    parts_unique.add(f'{msgKey}')

                    # *** 你要開發的Block在這裡 [End] ***

            # 打印出最更新的結果 <---- "題目#13" 的答案
            print(f'Parts of translog: ' + '|'.join(sorted(parts_unique)))

            # 觀察Consumer是否己經抵達topic/partiton的最尾端的offset
            # 如果程式己經把現在topic裡有的訊息全部都吃進來你看到的結果就是問題的答案

    except KeyboardInterrupt as e:
        sys.stderr.write('Aborted by user\n')
    except KafkaException as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)

    finally:
        # 步驟6.關掉Consumer實例的連線
        consumer.close()
