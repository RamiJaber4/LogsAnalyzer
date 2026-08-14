from processing_logs import LogParser, MetricsCalculator
def test_interpret_log():
    parser= LogParser()

    line= "2026-07-14 10:02:10,ERROR,auth,85,Login success user=15"
    result= parser.interpretLog(line)

    assert result.component == "auth"
    assert result.level == "error"
    assert result.msg == "Login success user=15"
    assert result.response_time == 85
    assert result.timestamp == "2026-07-14 10:02:10"

def test_process_log():
    calc= MetricsCalculator()
    parser= LogParser()

    # first log (error)

    line= "2026-07-14 10:02:10,ERROR,auth,85,Login success user=15"
    first_log= parser.interpretLog(line)
    
    calc.process_log(first_log)
    assert calc.total_response == 85
    assert calc.total_requests == 1
    assert calc.errors == 1

    assert calc.components.get(first_log.component).requests == 1
    assert calc.components.get(first_log.component).total_response == 85
    assert calc.components.get(first_log.component).avg_response == 85
    assert calc.components.get(first_log.component).errors == 1

    # second log (error)

    line = "2026-07-14 10:02:00,ERROR,auth,5000,Connection timeout trying to reach read-replica-01"
    second_log = parser.interpretLog(line)
    calc.process_log(second_log)
    assert calc.total_response == 5085
    assert calc.total_requests == 2
    assert calc.errors == 2
    

    assert calc.components.get(second_log.component).requests == 2
    assert calc.components.get(second_log.component).total_response == 5085
    assert calc.components.get(second_log.component).avg_response == 2542.5
    assert calc.components.get(second_log.component).errors == 2

    # third log (not error)
    line = "2026-07-14 10:01:15,INFO,payment,320,Transaction initiated user=12"
    third_log = parser.interpretLog(line)
    calc.process_log(third_log)
    assert calc.total_response == 5405
    assert calc.total_requests == 3
    assert calc.errors == 2

    assert calc.components.get(third_log.component).requests == 1
    assert calc.components.get(third_log.component).total_response == 320
    assert calc.components.get(third_log.component).avg_response == 320
    assert calc.components.get(third_log.component).errors == 0    

def test_reset_metrics():
    calc = MetricsCalculator()
    parser= LogParser()

    line = "2026-07-14 10:02:00,ERROR,auth,5000,Connection timeout trying to reach read-replica-01"
    first_log= parser.interpretLog(line)
    calc.process_log(first_log)

    line = "2026-07-14 10:01:15,INFO,payment,320,Transaction initiated user=12"
    second_log= parser.interpretLog(line)
    calc.process_log(second_log)

    calc.reset_metrics_obj()
    assert calc.errors == 0
    assert calc.total_requests == 0
    assert calc.total_response == 0