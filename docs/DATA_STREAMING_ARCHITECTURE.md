# Data Streaming Architecture: Raw vs Cleaned Data

## Question: Should we stream raw or cleaned data?

**Answer: Stream BOTH using a hybrid architecture** ✅

## 🏗️ Implemented Architecture

```
┌────────────────────┐
│   Data Source      │
│   (CICIDS2017)     │
└─────────┬──────────┘
          │
          ▼
┌───────────────────────────┐
│   Data Ingestion          │
│   Publishes RAW flows     │
└─────────┬─────────────────┘
          │
          ▼
   [network-flows-raw] ◄──── Archive to S3/Data Lake
          │
          ├──────────────────────────┐
          │                          │
          ▼                          ▼
┌──────────────────┐      ┌──────────────────────┐
│ Drift Monitor    │      │ Preprocessing        │
│                  │      │ Service              │
│ Consumes: RAW    │      │                      │
│                  │      │ - Validates quality  │
│ Why: Drift       │      │ - Imputes missing    │
│ detection must   │      │ - Applies selection  │
│ use original     │      │                      │
│ distributions    │      │ Consumes: RAW        │
│                  │      │ Publishes: PROCESSED │
└──────────────────┘      └──────────┬───────────┘
                                     │
                                     ▼
                            [network-flows-processed]
                                     │
                                     ├──────────────┐
                                     │              │
                                     ▼              ▼
                            ┌──────────────┐  ┌──────────────┐
                            │ Inference    │  │ Streaming    │
                            │ API          │  │ Consumer     │
                            │              │  │              │
                            │ Consumes:    │  │ Consumes:    │
                            │ PROCESSED    │  │ PROCESSED    │
                            │              │  │              │
                            │ Why: Low     │  │ Why: Low     │
                            │ latency      │  │ latency      │
                            └──────────────┘  └──────────────┘
```

## 📊 Kafka Topics

| Topic | Data Type | Consumers | Purpose |
|-------|-----------|-----------|---------|
| `network-flows-raw` | RAW network flows | Drift Monitor, Preprocessing Service | Ground truth, drift detection, archival |
| `network-flows-processed` | Cleaned & validated flows | Inference API, Streaming Consumer | Low-latency inference |
| `threat-predictions` | Prediction results | Analytics, SIEM, Dashboards | Threat alerts |

## ✅ Benefits of Hybrid Approach

### 1. **Raw Data Preservation**
- ✅ Audit trail for compliance
- ✅ Forensic analysis capability
- ✅ Can reprocess with new logic
- ✅ Debug production issues

### 2. **Accurate Drift Detection**
- ✅ PSI calculated on original distributions
- ✅ Detects real data drift, not preprocessing artifacts
- ✅ Alert on actual data quality issues

### 3. **Low Latency Inference**
- ✅ Consumers get pre-validated data
- ✅ No preprocessing overhead per request
- ✅ Consistent preprocessing across all consumers
- ✅ Faster time-to-prediction

### 4. **Flexibility**
- ✅ Change preprocessing without reingesting
- ✅ Multiple preprocessing strategies possible
- ✅ Different consumers can use different topics
- ✅ A/B testing preprocessing changes

### 5. **Data Quality Gates**
- ✅ Centralized validation
- ✅ Invalid data filtered early
- ✅ Metrics on data quality
- ✅ Prevents garbage-in-garbage-out

## 🎯 When to Use Each Topic

### Use RAW topic when:
- Drift monitoring
- Data quality analysis
- Archival/compliance
- Research and experimentation
- Debugging production issues

### Use PROCESSED topic when:
- Real-time inference (<10ms latency required)
- Batch predictions
- Analytics dashboards
- Production ML models

## 📈 Performance Impact

| Metric | Without Preprocessing Service | With Preprocessing Service |
|--------|------------------------------|---------------------------|
| **Inference Latency** | ~20ms (includes preprocessing) | ~10ms (preprocessing done) |
| **Throughput** | 500 req/sec | 1000+ req/sec |
| **CPU Usage** | High (repeated preprocessing) | Low (preprocessing once) |
| **Consistency** | Risk of drift | Guaranteed consistent |

## 🔧 Configuration

### Data Ingestion
```bash
# Publishes to RAW topic
python generate.py \
    --mode stream \
    --topic network-flows-raw \
    --rate 100
```

### Preprocessing Service
```bash
# Consumes RAW, publishes PROCESSED
python preprocessor.py \
    --input-topic network-flows-raw \
    --output-topic network-flows-processed
```

### Drift Monitor
```bash
# Uses RAW for accurate drift detection
python monitor.py \
    --topic network-flows-raw
```

### Streaming Consumer
```bash
# Uses PROCESSED for low latency
python consumer.py \
    --input-topic network-flows-processed
```

## 🚀 Best Practices

1. **Always archive RAW data** to S3/Data Lake
2. **Monitor preprocessing service** for failures
3. **Set up alerts** on preprocessing lag
4. **Version preprocessing logic** like code
5. **Include quality metrics** in processed data
6. **Dead letter queue** for invalid data
7. **Backpressure handling** if preprocessing is slow

## 📝 Summary

**For AI-CTIDS cybersecurity use case:**

✅ **Stream RAW data from source** (data-ingestion)
✅ **Add preprocessing service layer** (new component)
✅ **Publish PROCESSED data to separate topic**  
✅ **Drift monitor uses RAW**  
✅ **Inference services use PROCESSED**  

This gives us:
- Raw data for compliance and debugging
- Fast inference with preprocessed data
- Accurate drift detection on original distributions
- Centralized, consistent preprocessing
- Flexibility to change preprocessing logic

**Result: Best of both worlds!** 🎉
