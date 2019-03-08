import cx_Oracle
import functools
import time
import urllib.request

lengthtest = 1000
lengthtestquery = 250000
lengthtesturl = 10000

db_hostname = 'localhost'
db_port = '1521'
db_sid = 'XE'
db_username = 'TESTUSER'
db_password = 'TESTUSER'

dbstring = db_username + '/' + db_password + '@' + db_hostname + ':' + db_port + '/' + db_sid

def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)))
    return newfunc

@timeit
def runtestcon():
    for x in range(lengthtest):
        con = cx_Oracle.connect(dbstring)
        cur = con.cursor()
        cur.execute('select to_char(systimestamp) from dual')
        res=cur.fetchone()
        con.close()
        percentage=((x/lengthtest))*100
        if percentage>0 and percentage % 10==0:
            print (str(int(percentage))+' ',end='')
    print ('100')

@timeit
def runtestindb(con):
    for x in range(lengthtestquery):
        cur = con.cursor()
        cur.execute('select to_char(systimestamp) from dual')
        res=cur.fetchone()
        percentage=((x/lengthtestquery))*100
        if percentage>0 and percentage % 10==0:
            print (str(int(percentage))+' ', end='')
    print ('100')

def runtest_prep(cur):
    statement = """
       BEGIN

        execute immediate('CREATE SEQUENCE test_seq START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE');

        EXECUTE IMMEDIATE ('CREATE TABLE test_tab(
        test_id NUMBER,
        kolom VARCHAR2(50) NOT NULL,
        PRIMARY KEY(test_id))');

        execute immediate('CREATE TRIGGER test_trg
        BEFORE INSERT OR UPDATE ON test_tab
            FOR EACH ROW
            BEGIN
                :NEW.test_id := test_seq.NextVal;
            END;');
        END;"""
    cur.execute(statement)

def runtest_clean(cur):
    statement = """
       BEGIN
        begin
        execute immediate ('drop trigger test_trg');
        exception
        when others then
        null;
        end;

        begin
        execute immediate ('drop sequence test_seq');
        exception
        when others then
        null;
        end;

        begin
        execute immediate ('drop table test_tab');
        exception
        when others then
        null;
        end;

        END;"""
    cur.execute(statement)

@timeit
def runtestcreateremoveobjects(cur):
    for x in range(lengthtest):
        runtest_prep(cur)
        runtest_clean(cur)
        percentage=((x/lengthtest))*100
        if percentage>0 and percentage % 10==0:
            print (str(int(percentage))+' ', end='')
    print ('100')

@timeit
def runtestinsdel(cur):
    statement = """
       BEGIN
        FOR loop_counter IN 1..300
        LOOP
        insert into test_tab(kolom) values ('Hallo');
        END LOOP;
        commit;
        delete from test_tab;
        commit;
       END;"""
    for x in range(lengthtest):
        cur.execute(statement)
        percentage=((x/lengthtest))*100
        if percentage>0 and percentage % 10==0:
            print (str(int(percentage))+' ', end='')

@timeit
def runtestinsdelcommit(cur):
    statement = """
       DECLARE
        l_testid test_tab.test_id%type;
       BEGIN
        FOR loop_counter IN 1..200
        LOOP
        insert into test_tab(kolom) values ('Hallo') returning test_id into l_testid;
        commit;
        delete from test_tab where test_id = l_testid;
        commit;
        END LOOP;
       END;"""
    for x in range(lengthtest):
        cur.execute(statement)
        percentage=((x/lengthtest))*100
        if percentage>0 and percentage % 10==0:
            print (str(int(percentage))+' ', end='')

def createpublicproc(cur):
    statement = """
    create or replace
    procedure
    TEST_PROC
    AUTHID
    CURRENT_USER as
    BEGIN
    Begin
    HTP.htmlopen;
    HTP.headopen;
    HTP.title('This is a test page!');
    HTP.headclose;
    HTP.bodyopen;
    HTP.print('This is a test page! DateTime: ' || TO_CHAR(SYSTIMESTAMP) || ' User: '||user);
    HTP.bodyclose;
    HTP.htmlclose;
    end;
    END;"""
    cur.execute(statement)
    statement = "grant execute on TEST_PROC to public"
    cur.execute(statement)

def removepublicproc(cur):
    statement = "drop procedure TEST_PROC"
    cur.execute(statement)

def getdadporturl(cur):
    statement="""
        create or replace procedure tmp_proc(p_path out varchar2,p_port out varchar2) as
            l_paths  DBMS_EPG.varchar2_table;
            l_dadname dba_epg_dad_authorization.dad_name%TYPE;
        BEGIN
            select dad_name into l_dadname from dba_epg_dad_authorization where rownum=1;
            SELECT to_char(DBMS_XDB.GETHTTPPORT) into p_port FROM DUAL;
            DBMS_EPG.get_all_dad_mappings (
                dad_name => l_dadname,
                paths    => l_paths);
            FOR i IN 1 .. l_paths.count LOOP
                p_path := replace(l_paths(i),'/*','');
            END LOOP;
        END;
    """
    cur.execute(statement)
    l_port = cur.var(cx_Oracle.STRING)
    l_path = cur.var(cx_Oracle.STRING)
    cur.callproc('tmp_proc', [l_path, l_port])
    statement = """
            BEGIN
                execute immediate 'drop procedure tmp_proc';
            END;
        """
    cur.execute(statement)
    return l_port.getvalue(), l_path.getvalue()

@timeit
def urltest(url_to_call):
    for x in range(lengthtesturl):
        contents = urllib.request.urlopen(url_to_call).read()
        percentage = ((x / lengthtesturl)) * 100
        if percentage > 0 and percentage % 10 == 0:
            print(str(int(percentage)) + ' ', end='')

print('Testing create connection, create cursor, query, close connection')
runtestcon()

print('Testing create cursor, query,')
con = cx_Oracle.connect(dbstring)
runtestindb(con)
con.close()

print('Testing creating and removing objects');

con = cx_Oracle.connect(dbstring)
cur = con.cursor()
runtest_clean(cur)
runtestcreateremoveobjects(cur)
con.close()

print('Inserting data, commit, deleting data, commit');
con = cx_Oracle.connect(dbstring)
cur = con.cursor()
runtest_clean(cur)
runtest_prep(cur)
runtestinsdel(cur)
runtest_clean(cur)
con.close()

print('Inserting single row, commit, delete single row, commit');
con = cx_Oracle.connect(dbstring)
cur = con.cursor()
runtest_clean(cur)
runtest_prep(cur)
runtestinsdelcommit(cur)
runtest_clean(cur)
con.close()

print('Testing DAD EPG');
con = cx_Oracle.connect(dbstring)
cur = con.cursor()
createpublicproc(cur)
dad_port, endpoint = getdadporturl(cur)
url_to_call = "http://"+db_hostname+':'+dad_port+endpoint+'/'+db_username+'.TEST_PROC'
print ("Using: "+url_to_call)
urltest(url_to_call)
removepublicproc(cur)
con.close()
