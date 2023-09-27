# clinicalETL
In medical research, health data of human beings is essential. It forms the basis for the creation and confirmation of new hypotheses. Up to now, data to a large extent have been generated in specific studies for this purpose. A much larger amount of medical data is already being collected digitally at many healthcare institutions in the care of patients. The storage of this data takes place on proprietarily implemented databases, which are not designed for research regarding their structure, content and functionality. Accessing these data pools would drive research forward immensely.

The research group "MedDigit - Medizin und Digitalisierung" of the Department of Neurology at the University Hospital Magdeburg is specialized in the computer-aided processing of medical data. In order to make the clinical data available to the MedDigit research group, a data integration process and a database designed for research are conceptualized and implemented. The data pool of the database for clinical routine data of the Clinic for Neurology of the University Hospital Magdeburg is analysed. Thereby a selection, filtering, anonymisation and pseudonymisation of the data is performed. By integrating the developed processes and the new database into the system of the research group, clinical routine data of the Clinic for Neurology of the University Hospital Magdeburg is available for research for the first time.

This project enables the use of clinical patient and event data created as part of the clinical routine work for research purposes at the Department of Neurology at University Hospital Magdeburg. It performs a complete ETL process, starting from reading CSV data to selection, filtering, anonymization, and pseudonymization for strong patient confidentiality, and ending with the loading of transformed and sanitized data into a separate PostgreSQL database.  

Contains source code, scripts, and software configs created as part of my bachelor's thesis.

<br/>
<br/>

![pipeline](https://github.com/CuratorCodicis/clinicalETL/assets/146182825/49e6b31c-622b-4591-a098-1dbc4b740b24)
