#!/bin/bash
# Cron wrapper for stock pulls — all 4 entities, sequential
# Runs daily at 05:00 WIB (before business hours)
# Logs to /opt/openclaw/logs/stock_YYYYMMDD.log
# Status file: /opt/openclaw/logs/stock_latest_status.json

VENV=/opt/openclaw/venv/bin/python
SCRIPT=/opt/openclaw/scripts/pull_accurate_stock.py
LOGDIR=/opt/openclaw/logs
DATE=$(date +%Y%m%d)
LOGFILE=$LOGDIR/stock_$DATE.log
STATUS_FILE=$LOGDIR/stock_latest_status.json

echo "========================================" >> $LOGFILE
echo "STOCK PULL START: $(date '+%Y-%m-%d %H:%M:%S WIB')" >> $LOGFILE
echo "========================================" >> $LOGFILE

# Track results
RESULTS="{}"
ALL_OK=true

for ENTITY in ddd ljbb mbb ubb; do
    echo "" >> $LOGFILE
    echo "--- $ENTITY ---" >> $LOGFILE
    START_TIME=$(date +%s)
    
    $VENV $SCRIPT $ENTITY >> $LOGFILE 2>&1
    EXIT_CODE=$?
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    if [ $EXIT_CODE -eq 0 ]; then
        STATUS="success"
    else
        STATUS="error"
        ALL_OK=false
    fi
    
    echo "  $ENTITY: $STATUS (exit=$EXIT_CODE, ${DURATION}s)" >> $LOGFILE
done

echo "" >> $LOGFILE
echo "========================================" >> $LOGFILE
echo "STOCK PULL END: $(date '+%Y-%m-%d %H:%M:%S WIB')" >> $LOGFILE
echo "========================================" >> $LOGFILE

# Write status file for Atlas to check
if $ALL_OK; then
    OVERALL="success"
else
    OVERALL="partial_error"
fi

cat > $STATUS_FILE << STATUSEOF
{
  "type": "stock_pull",
  "date": "$(date +%Y-%m-%d)",
  "time": "$(date '+%H:%M:%S')",
  "overall": "$OVERALL",
  "log_file": "$LOGFILE"
}
STATUSEOF

echo "Status written to $STATUS_FILE"
