import csv
import datetime
from argparse import ArgumentParser
from dataclasses import dataclass, field
from datetime import datetime, date
import os
from pathlib import Path
import sys
from urllib.parse import urljoin

from dateparser import parse
import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict

from Person import Person
from Earnings import Earnings

thisdir = Path(__file__).parent.absolute()
outer_dir = thisdir.parent
sys.path.append(os.path.abspath(outer_dir))
import hris_utils
logger = hris_utils.get_logger(thisdir / 'UKG_log.log')
print = logger.info

# UTILITY FUNCTIONS
def formatDate(dateTimeStr):
    if not dateTimeStr:
        return ""
    dateTime = datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%S')
    date = dateTime.strftime('%Y%m%d')
    return date

def dateAfterStartDate(dateTimeStr):
    dateTime = datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%S')
    dateTime2 = hris_utils.START_DATE(2)
    return dateTime2 <= dateTime

def parseDatestring(ds: str):
    if ds in ['', None]:
        return datetime.today()
    return parse(ds)

def downloadData(url, header, params=dict()):
    '''Retrieves JSON data from API with auth keys in header'''
    params['per_page'] = "10000"
    dataDownloadComplete = False
    while dataDownloadComplete == False:
        try:
            response = requests.get(url, headers=header, params=params)
            logger.debug(f'{response.url}')
            logger.debug(f'{response.text}')
            data = response.json()
            dataDownloadComplete = True
        except requests.exceptions.Timeout:
            print("Connection timed out")
            print("Retrying...")
        except requests.exceptions.ConnectionError:
            print("Connect Error")
            print("Retrying...")
        except requests.exceptions.ConnectTimeout:
            print("Connect Timeout")
            print("Retrying...")
        except Exception as e:
            logger.error(f'Connect issue: {e}')
    return data

@dataclass
class Company():
    company_name: str
    company_id: str
    service: int
    api_key: str
    auth_token: str
    filename_extension: str = ""
    output_format: int = 0
    resultsdir: Path = Path.cwd()
    header: dict = field(default_factory=CaseInsensitiveDict)
    people: list[Person] = field(default_factory=list)
    employeeEarnings: list[Earnings] = field(default_factory=list)
    payGroups: set = field(default_factory=set)

    def __post_init__(self):
        #https://developer.ukg.com/hcm/reference/welcome-to-the-pro-developer-hub
        self.header = { 
            "US-Customer-Api-Key": self.api_key,
            "Authorization" : f"Basic {self.auth_token}"
            }
            #Class variables
        self.service = int(self.service)
        self.rootUrl = {
            4: "https://service4.ultipro.com",
            5: "https://service5.ultipro.com"
            }[self.service]
        self.personDetailsUrl = urljoin(self.rootUrl, f"/personnel/v1/companies/{self.company_id}/person-details")
        self.compensationDetailsUrl = urljoin(self.rootUrl, f"/personnel/v1/companies/{self.company_id}/compensation-details")
        self.employmentDetailsUrl = urljoin(self.rootUrl, f"/personnel/v1/companies/{self.company_id}/employment-details")
        self.payRollDetailsUrl = urljoin(self.rootUrl, f"/payroll/v1/earnings-history-base-elements?companyID={self.company_id}")

    def findPersonById(self, employeeId):
        for person in self.people:
            if person.employeeID == employeeId:
                return person

    def findPersonByNumber(self, employeeNum):
        for person in self.people:
            if person.employeeNumber == employeeNum:
                return person

    def getPersonDetails(self, testJSON=None):
        print(f'Retrieving {self.company_name} employees')
        peopleJSON = downloadData(self.personDetailsUrl, self.header) if testJSON is None else testJSON
        for personData in peopleJSON:
            person = Person()
            try:
                person.employeeID = personData["employeeId"]
                person.firstName = personData["firstName"]
                person.middleName = personData["middleName"]
                person.lastName = personData["lastName"]
                person.suffix = personData["nameSuffixCode"]
                person.formerLastName = personData["formerName"]
                person.SSN = personData["ssn"]
                person.emailAddress = personData["emailAddress"]
                person.emailAddressAlt = personData["emailAddressAlternate"]
                person.phoneNumber = personData["homePhone"]
                person.dateOfBirth = formatDate(personData["dateOfBirth"])

                self.people.append(person)
            except Exception as e:
                print(f"An exception occurred while getting Employees: {e}") 
        return None 

    def getCompensationDetails(self, testJSON=None):
        print('Retrieving compensation details')
        compensationJSON = downloadData(self.compensationDetailsUrl, self.header) if testJSON is None else testJSON
        
        # Ingest compensation data into a dataframe & group records by employee
        df = pd.json_normalize(compensationJSON)
        desired_cols = ['employeeID', 'salaryOrHourlyCode', 'hourlyPayRate', 'annualSalary', 'emplStatus', 'dateLastWorked', 'payGroupCode']
        df2 = df[desired_cols]
        df2['dateLastWorked2'] = df['dateLastWorked'].apply(parseDatestring)
        # Retain the most recent compensation record for an employee, based on latest change
        # Preferred: 'Active'.   If all 'Terminated', use date last worked
        keep = df2.groupby('employeeID')['dateLastWorked2'].idxmax()
        df_compensation = df2.loc[keep]
        
        for compensationData in list(df_compensation.itertuples()):
            try:
                person = self.findPersonById(compensationData.employeeID)
                if person is not None:
                    person.salaryCode =  compensationData.salaryOrHourlyCode
                    person.hourlyPayRate = compensationData.hourlyPayRate
                    person.salaryPayRate = compensationData.annualSalary
                    person.payType = compensationData.salaryOrHourlyCode
                    person.status = compensationData.emplStatus

                    self.payGroups.add(compensationData.payGroupCode)
                    
            except Exception as e:
                print(f"An exception occurred while getting Compensation details: {e}")  
        return None

    def getEmploymentDetails(self, testJSON=None):
        print('Retrieving Employment details')
        employmentJSON = downloadData(self.employmentDetailsUrl, self.header) if testJSON is None else testJSON
        # Ingest employment data into a dataframe & group records by employee
        df = pd.json_normalize(employmentJSON)
        desired_cols = ['employeeID', "employeeNumber", "companyCode", 'jobDescription', 'jobTitle', "scheduledWorkHrs", "originalHireDate", "lastHireDate", "dateOfTermination", 'dateTimeChanged', 'statusStartDate']
        updated_col_names = ['employeeID', "employeeNumber", "companyCode", 'jobDescription', 'jobTitle', "scheduledWorkHrs", "originalHireDate", "lastAdjustedHireDate", "terminationDate", 'dateTimeChanged', 'employmentStatusStartDate']
        df2 = df[desired_cols]
        df2.columns = updated_col_names
        df2['dateTimeChanged2'] = df['dateTimeChanged'].apply(parseDatestring)
        # Retain the most recent employment record for an employee, based on latest change
        keep = df2.groupby('employeeID')['dateTimeChanged2'].idxmax()
        df_employment = df2.loc[keep]
        #DEBUGGING OUTPUTS
        #df.to_csv(r'C:\Users\pjsmole\Documents\GitHub\U-Jason-Merge\Test Data\BGCSTL\raw_emp.csv')
        #df3.to_csv(r'C:\Users\pjsmole\Documents\GitHub\U-Jason-Merge\Test Data\BGCSTL\unfiltered_emp.csv')
        #df_employment.to_csv(r'C:\Users\pjsmole\Documents\GitHub\U-Jason-Merge\Test Data\BGCSTL\filtered_emp.csv')
        
        for employmentData in list(df_employment.itertuples()):
            try:
                person = self.findPersonById(employmentData.employeeID)
                if person is not None:
                    person.employeeNumber = employmentData.employeeNumber
                    person.companyCode = employmentData.companyCode
                    person.jobTitle = employmentData.jobTitle if employmentData.jobTitle is not None else employmentData.jobDescription
                    person.scheduledWorkHours = employmentData.scheduledWorkHrs
                    person.originalHireDate = formatDate(employmentData.originalHireDate)
                    person.lastAdjustedHireDate = formatDate(employmentData.lastAdjustedHireDate)
                    person.terminationDate = formatDate(employmentData.terminationDate)
            except Exception as e:
                print(f"An exception occurred while getting Employment details: {e}") 
        return None

    def getPayGroupPayrollDetails(self, payGroup):
        payRollJSON = downloadData(self.payRollDetailsUrl, header=self.header, params={"payGroup":payGroup})
        for payRollData in payRollJSON:
            try:
                if not dateAfterStartDate(payRollData["payDate"]):
                    continue
                if self.findPersonByNumber(payRollData["employeeNumber"]) is None:
                    continue

                employeePeriodEarnings = Earnings()
                person = self.findPersonById(payRollData["employeeId"])
                if person is not None:
                    employeePeriodEarnings.companyCode = person.companyCode
                    employeePeriodEarnings.SSN = person.SSN

                employeePeriodEarnings.employeeNumber = payRollData["employeeNumber"]
                employeePeriodEarnings.earningCode = payRollData["earningCode"]
                employeePeriodEarnings.payDate = formatDate(payRollData["payDate"])
                employeePeriodEarnings.baseAmout = payRollData["baseAmount"]

                self.employeeEarnings.append(employeePeriodEarnings)
            except Exception as e:
                print(f"An exception occurred in getting {payGroup} data: {e}") 
        return None
 
    def createEmployeeDataOutput2CSVFile(self):
        print("Writing Data to EmployeeData2 .csv File...")

        with open(self.resultsdir / f'{self.filename_extension}-EmployeeData2-{date.today()}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            headerData = [  "Record Type", "First Name", "Middle Name", "Last Name", "Former Last Name", "Suffix", "EmpNumCompCd", 
                            "Supervisor Name", "Job Title", "Employment Status", "Salary/Hourly Code", "Pay Rate", "Email", 
                            "Home Phone", "D.O.B.", "Original Hire Date", "Last Hire Date", "Scheduled Work Hours", "Termination Date", 
                            "Active Status", "Employee Status Start Date", "Status Expected End Date", 
                            "Custom1", "Custom2", "Custom3", "Custom4", "Custom5"]
            writer.writerow(headerData) 

            employeeNum = ""
            for person in self.people:
                if self.output_format == 1:
                    employeeNum = person.employeeNumberCompanyCode()
                else:
                    employeeNum = person.employeeNumber
                rowData = [ person.recordType, person.firstName, person.middleName, person.lastName, person.formerLastName, 
                            person.suffix,  employeeNum, person.supervisorName, person.jobTitle, person.employmentStatusFull(), 
                            person.salaryCode, person.getSalaryOrHourlyRate(), person.emailAddress, person.phoneNumber, 
                            person.dateOfBirth, person.originalHireDate, person.lastAdjustedHireDate, person.scheduledWorkHours, 
                            person.terminationDate, person.activeStatus(), person.employmentStatusStartDate, person.statusExpectedEndDate, 
                            person.custom1, person.custom2, person.custom3, person.custom4, person.custom5]
                writer.writerow(rowData)
                #person.print()
        #file.close()
 
    def createEmployeePaymentDataOutput2CSVFile(self):
        print("Writing Data to EmployeePayData2 .csv File...")

        with open(self.resultsdir / f'{self.filename_extension}-EmployeePayData-{date.today()}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            headerData = ["Record Type", "Employee #", "Earnings Code", "Pay Date", "Base Amount"]
            writer.writerow(headerData)
            
            employeeNum = ""
            for earnings in self.employeeEarnings:
                if self.output_format == 1:
                    employeeNum = earnings.employeeNumberCompanyCode()
                else:
                    employeeNum = earnings.employeeNumber
                
                rowData = [earnings.recordType, employeeNum, earnings.earningCode, earnings.payDate, earnings.baseAmout]
                writer.writerow(rowData)
                #earnings.print()
        #file.close()

    def collectCompanyData(self):
        logger.info(f"Downloading {self.company_name} Employee data...")
        self.getPersonDetails()
        self.getCompensationDetails()
        self.getEmploymentDetails()

        logger.info(f"Employees Downloaded: {len(self.people)}")
        logger.info(f"Downloading {self.company_name} Employee Pay data since {hris_utils.START_DATE(2):%b %Y}...")    
        
        for payGroup in self.payGroups:
            logger.info(f"Retrieving pay group: {payGroup}")
            self.getPayGroupPayrollDetails(payGroup)

        logger.info(f"Employees Payments Stored: {len(self.employeeEarnings)}")
        self.employeeEarnings.sort(key = lambda e: e.employeeNumber, reverse = False)

        self.createEmployeeDataOutput2CSVFile()
        self.createEmployeePaymentDataOutput2CSVFile()
        return None


def main(COMPANIES=".ukg_companies.csv"):
    resultsdir = thisdir / 'UKG_Results'
    resultsdir.mkdir(parents=True, exist_ok=True)
    
    companyCSV = thisdir / COMPANIES
    df_companies,compIDs = hris_utils.get_user_input(companyCSV)
    if compIDs is None: 
        print('Exiting')
        return None
    for compID in compIDs:
        compInfo = df_companies.iloc[compID]
        compDict = compInfo.to_dict()
        compDict['resultsdir'] = resultsdir
        company = Company(**compDict)
        company.collectCompanyData()
    print('Al Fin')


if __name__ == "__main__":
    parser = ArgumentParser(description="Obtain HR data from UKG API")
    parser.add_argument("--test", action='store_true', help=f"Test: Uses test secrets files")
    args = parser.parse_args()
    if args.test:
        main(COMPANIES='.test_ukg_companies.csv')
    else:
        main()
