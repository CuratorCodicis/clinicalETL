-- Table: public."Patient"

-- DROP TABLE public."Patient";

CREATE TABLE public."Patient"
(
    "Pat_id" character varying COLLATE pg_catalog."default" NOT NULL,
    age integer,
    CONSTRAINT patient_pkey PRIMARY KEY ("Pat_id")
)

TABLESPACE pg_default;

ALTER TABLE public."Patient"
    OWNER to admin;
	
	
-- Table: public."Event"

-- DROP TABLE public."Event";

CREATE TABLE public."Event"
(
    "Event_id" character varying COLLATE pg_catalog."default" NOT NULL,
    "Pat_id" character varying COLLATE pg_catalog."default",
    "Category" integer,
    "Value_type_id" character(2) COLLATE pg_catalog."default",
    "Observation_id" character varying COLLATE pg_catalog."default",
    "Observation_txt" character varying COLLATE pg_catalog."default",
    "Observation_cs" character varying COLLATE pg_catalog."default",
    "Alternative_observation_id" character varying COLLATE pg_catalog."default",
    "Alternative_observation_txt" character varying COLLATE pg_catalog."default",
    "Alternative_observation_cs" character varying COLLATE pg_catalog."default",
    "Observation_ts" timestamp without time zone,
    "Observation_subid" character varying COLLATE pg_catalog."default",
    "Set_id" character varying COLLATE pg_catalog."default",
    "Id_obr" character varying COLLATE pg_catalog."default",
    "Unit_id" character varying COLLATE pg_catalog."default",
    "Unit_txt" character varying COLLATE pg_catalog."default",
    "Unit_cs" character varying COLLATE pg_catalog."default",
    "Reference_range" character varying COLLATE pg_catalog."default",
    "Result_status_id" character varying COLLATE pg_catalog."default",
    "Event_age" integer,
    CONSTRAINT event_pkey PRIMARY KEY ("Event_id"),
    CONSTRAINT "patient id" FOREIGN KEY ("Pat_id")
        REFERENCES public."Patient" ("Pat_id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public."Event"
    OWNER to admin;
	
	
-- Table: public."Value_nm"

-- DROP TABLE public."Value_nm";

CREATE TABLE public."Value_nm"
(
    "Event_id" character varying COLLATE pg_catalog."default" NOT NULL,
    "Value" double precision,
    CONSTRAINT "Value_nm_pkey" PRIMARY KEY ("Event_id"),
    CONSTRAINT "Event ID" FOREIGN KEY ("Event_id")
        REFERENCES public."Event" ("Event_id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public."Value_nm"
    OWNER to admin;
	
	
-- Table: public."Value_tx"

-- DROP TABLE public."Value_tx";

CREATE TABLE public."Value_tx"
(
    "Event_id" character varying COLLATE pg_catalog."default" NOT NULL,
    "Value" character varying COLLATE pg_catalog."default",
    CONSTRAINT "Value_string_pkey" PRIMARY KEY ("Event_id"),
    CONSTRAINT "Event ID" FOREIGN KEY ("Event_id")
        REFERENCES public."Event" ("Event_id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public."Value_tx"
    OWNER to admin;


-- Table: public."Dictionary"

-- DROP TABLE public."Dictionary";

CREATE TABLE public."Dictionary"
(
    "Name" character varying COLLATE pg_catalog."default" NOT NULL,
    "Bez" character varying COLLATE pg_catalog."default",
    "Dialogfenster" character varying COLLATE pg_catalog."default",
    "Oberbegriff" character varying COLLATE pg_catalog."default",
    "Category" integer,
    "Kind" character(2) COLLATE pg_catalog."default",
    "Repkind" character(2) COLLATE pg_catalog."default",
    "Units" character varying COLLATE pg_catalog."default",
    "Share_id" character varying COLLATE pg_catalog."default",
    "Sort_order" character varying COLLATE pg_catalog."default",
    "Id" character varying COLLATE pg_catalog."default",
    "Admin" character varying COLLATE pg_catalog."default",
    "Obclass" character varying COLLATE pg_catalog."default",
    "Codingsystem" character varying COLLATE pg_catalog."default",
    CONSTRAINT "Dictionary_pkey" PRIMARY KEY ("Name")
)

TABLESPACE pg_default;

ALTER TABLE public."Dictionary"
    OWNER to admin;