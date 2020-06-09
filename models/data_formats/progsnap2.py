import csv
import os
import tempfile
from datetime import datetime
import io
import time

from natsort import natsorted
from tqdm import tqdm

from models.assignment_group import AssignmentGroup
from models.course import Course
from models.log import Log
from models.user import User

PROGSNAP_CSV_WRITER_OPTIONS = {'delimiter': ',', 'quotechar': '"', 'quoting': csv.QUOTE_MINIMAL}

# TODO: Investigate filenames of instructor files - shouldn't they be _instructor/*?

def generate_readme(zip_file):
    zip_file.writestr("Readme.txt", "Generated from BlockPy")
    return "Readme.txt"


def generate_metadata(zip_file):
    with io.StringIO() as metadata_file:
        writer = csv.writer(metadata_file, **PROGSNAP_CSV_WRITER_OPTIONS)
        writer.writerow(["Property", "Value"])
        writer.writerow(["Version", "6"])
        writer.writerow(["IsEventOrderingConsistent", "false"])
        writer.writerow(["CodeStateRepresentation", "Directory"])
        zip_file.writestr("DatasetMetadata.csv", metadata_file.getvalue())
        return "DatasetMetadata.csv"


'''
# Identification
assignment_id = Column(Integer(), ForeignKey('assignment.id'))
assignment_version = Column(Integer())
course_id = Column(Integer(), ForeignKey('course.id'))
subject_id = Column(Integer(), ForeignKey('user.id'))
# Actual event data
event_type = Column(String(255))
file_path = Column(String(255), default="", nullable=True)
category = Column(String(255), default="")
label = Column(String(255), default="")
# Message will be JSON encoded data
message = Column(Text(), default="")
client_timestamp = Column(String(255), default="")
client_timezone = Column(String(255), default="")

assignment = db.relationship("Assignment")
subject = db.relationship("User")
course = db.relationship("Course")

# event_type
# => event_id
# subject_id
# => tool_instances
# => code_state_id
# => server_timestamp
# => server_timezone
# client_timestamp
# => client_timezone
# => session_id
# course_id
# => term_id
# assignment_id
# => edit_type
# file_path
# ? body
# => execution_result
# => SyntaxError: compile_result, compile_message_type, compile_message_data
# => Feedback: intervention_type, intervention_message
# => RunTime Error: program_input, program_output, program_error_output
# => source_location (line of code with error)
# => score
'''


def blockpy_timestamp_to_iso8601(timestamp):
    """
    Converts blockpy style timestamps into an ISO-8601 compatible timestamp.

    > blockpy_timestamp_to_iso8601(2018-10-31-12-02-25)
    2018-10-31T12:02:25

    Arguments:
        timestamp (str): A blockpy-style timestamp
    Returns:
        str: The ISO-8601 timestamp.
    """
    if not timestamp:
        return ""
    return datetime.fromtimestamp(int(timestamp) / 1000).isoformat()


HEADERS = [
    'EventID', 'Order', 'SubjectID', 'AssignmentID', 'CourseID',
    'EventType', 'CodeStateID',
    'ParentEventID',
    'ClientTimestamp', 'ClientTimezone',
    'Score',
    'EditType',
    'CompileMessageType', 'CompileMessageData', 'CodeStateSection',
    'InterventionCategory', 'InterventionType', 'InterventionMessage',
    'ServerTimestamp', 'ServerTimezone', 'ToolInstances'
]

TOOL_INSTANCE_ID = "BPY5"

CODE_STATE_UPDATE_EVENT_TYPES = {
    "File.Edit": "GenericEdit",
    "X-File.Add": "GenericEdit",
    "X-Instructor.File.Edit": "GenericEdit",
    "File.Create": "GenericEdit"
}


def to_progsnap_event(log, order_id, code_states, latest_code_states, scores):
    fields = [log.id, order_id, log.subject_id, log.assignment_id, log.course_id, log.event_type]
    submission_identification = (log.subject_id, log.assignment_id, log.course_id)
    # Figure out code_state
    current_code_base = latest_code_states.get(submission_identification, {})
    edit_type = ""
    if log.event_type in CODE_STATE_UPDATE_EVENT_TYPES:
        current_code_base[log.file_path] = log.message
        edit_type = CODE_STATE_UPDATE_EVENT_TYPES[log.event_type]
        latest_code_states[submission_identification] = current_code_base
    hashed_code_base = tuple(sorted(current_code_base.items()))
    if hashed_code_base in code_states:
        code_state_id = code_states[hashed_code_base]
    else:
        code_state_id = len(code_states)
        code_states[hashed_code_base] = code_state_id
    # Figure out score
    if log.event_type == "Intervention" and log.category == "Complete":
        scores[submission_identification] = score = 1
    elif log.event_type == "X-Submission.LMS":
        scores[submission_identification] = score = log.message
    else:
        score = ""
    # Compile Stuff
    if log.event_type == "Compile.Error":
        compile_message_type = "Error"
        compile_message_data = log.message
    else:
        compile_message_type = ""
        compile_message_data = ""
    # Intervention
    if log.event_type == "Intervention":
        intervention_category = "Feedback"
        intervention_type = log.category + "|" + log.label
        intervention_message = log.message
    else:
        intervention_category = ""
        intervention_type = ""
        intervention_message = ""
    # Result
    return fields + [code_state_id,
                     "",  # TODO: ParentEventId
                     blockpy_timestamp_to_iso8601(log.client_timestamp),
                     log.client_timezone,
                     score,
                     edit_type,
                     compile_message_type,
                     compile_message_data,
                     log.file_path,
                     intervention_category,
                     intervention_type,
                     intervention_message,
                     log.date_created.isoformat(),
                     str(time.timezone // 36).zfill(4),
                     TOOL_INSTANCE_ID
                     ]


def generate_maintable(zip_file, course_id, assignment_group_ids):
    code_states, latest_code_states, scores = {}, {}, {}
    query = Log.query.filter_by(course_id=course_id)
    if assignment_group_ids is not None:
        assignment_ids = [assignment.id
                          for group_id in assignment_group_ids
                          for assignment in AssignmentGroup.by_id(group_id).get_assignments()]
        query = query.filter(Log.assignment_id.in_(assignment_ids))
    estimated_size = query.count()
    logs = query.order_by(Log.date_created.asc()).yield_per(100)
    with io.StringIO() as maintable_file:
        writer = csv.writer(maintable_file, **PROGSNAP_CSV_WRITER_OPTIONS)
        writer.writerow(HEADERS)
        order_id = 0
        for log in tqdm(logs, total=estimated_size):
            writer.writerow(to_progsnap_event(log, order_id, code_states, latest_code_states, scores))
            order_id += 1
        zip_file.writestr("MainTable.csv", maintable_file.getvalue())
        return "MainTable.csv", code_states


def generate_link_subjects(zip_file, course_id):
    with io.StringIO() as linktable_file:
        writer = csv.writer(linktable_file, **PROGSNAP_CSV_WRITER_OPTIONS)
        writer.writerow(["SubjectID", "X-IsStaff", "X-Roles",
                         "X-Name.Last", "X-Name.First", "X-Email"])

        # Get any users explicitly in this course
        users_with_roles = Course.by_id(course_id).get_users()
        users, user_roles = {}, {}
        for role, user in users_with_roles:
            if user.id not in users:
                users[user.id] = user
                user_roles[user.id] = set()
            user_roles[user.id].add(role.name)

        # Get any additional users found in the logs
        log_users = Log.get_users_for_course(course_id)
        for log_user in log_users:
            if log_user.id not in users:
                users[log_user.id] = log_user
                user_roles[log_user.id] = {role.name for role in log_user.get_course_roles(course_id)}

        # Report their information
        for user_id, user in natsorted(users.items(), lambda u: (u[1].last_name, u[1].first_name)):
            roles = user_roles[user_id]
            display_roles = ", ".join(sorted(roles))
            writer.writerow([
                user.id,  # SubjectId
                bool(User.is_lti_instructor(roles)),  # X-IsStaff
                display_roles,  # X-Roles
                user.last_name,  # X-Name.Last
                user.first_name,  # X-Name.First
                user.email,  # X-Email
            ])
        zip_file.writestr("LinkTables/Subject.csv", linktable_file.getvalue())
        return "LinkTables/Subject.csv"


def generate_link_assignments(zip_file, course_id, assignment_group_ids):
    if assignment_group_ids is None:
        assignments = Log.get_assignments_for_course(course_id)
        all_groups = set()
        assignment_groups = {}
        for assignment in assignments:
            groups = AssignmentGroup.by_assignment(assignment.id)
            all_groups.update(groups)
            assignment_groups[assignment.id] = groups
    else:
        all_groups = [AssignmentGroup.by_id(group_id) for group_id in assignment_group_ids]
        assignment_groups = {}
        assignments = set()
        for group in all_groups:
            for assignment in group.get_assignments():
                if assignment.id not in assignment_groups:
                    assignment_groups[assignment.id] = set()
                assignment_groups[assignment.id].add(group)
                assignments.add(assignment)


    with io.StringIO() as assignment_file:
        assignment_writer = csv.writer(assignment_file, **PROGSNAP_CSV_WRITER_OPTIONS)
        assignment_writer.writerow(["AssignmentId", "X-Version",
                                    "X-Name", "X-URL", "X-Instructions",
                                    "X-Reviewed", "X-Hidden", "X-Settings",
                                    "X-Code.OnRun", "X-Code.OnChange", "X-Code.OnEval",
                                    "X-Code.Starting", "X-Code.ExtraInstructor", "X-Code.ExtraStarting",
                                    "X-Forked.Id", "X-Forked.Version",
                                    "X-Owner.Id", "X-Course.Id",
                                    "X-AssignmentGroup.Ids"])
        for assignment in natsorted(assignments, key=lambda a: a.name):
            assignment_writer.writerow([
                assignment.id, assignment.version,
                assignment.name, assignment.url, assignment.instructions,
                assignment.reviewed, assignment.hidden, assignment.settings,
                assignment.on_run, assignment.on_change, assignment.on_eval,
                assignment.starting_code, assignment.extra_instructor_files, assignment.extra_starting_files,
                assignment.forked_id, assignment.forked_version,
                assignment.owner_id, assignment.course_id,
                ", ".join(map(str, (g.id for g in assignment_groups[assignment.id])))
            ])

        zip_file.writestr("LinkTables/Assignment.csv", assignment_file.getvalue())
        yield "LinkTables/Assignment.csv"

    with io.StringIO() as group_file:
        group_writer = csv.writer(group_file, **PROGSNAP_CSV_WRITER_OPTIONS)
        group_writer.writerow(["AssignmentGroupId", "X-Version",
                               "X-Name", "X-URL",
                               "X-Forked.Id", "X-Forked.Version",
                               "X-Owner.Id", "X-Course.Id"])
        for group in natsorted(all_groups, key=lambda g: g.name):
            group_writer.writerow([
                group.id, group.version,
                group.name, group.url,
                group.forked_id, group.forked_version,
                group.owner_id, group.course_id,
            ])

        zip_file.writestr("LinkTables/AssignmentGroup.csv", group_file.getvalue())
        yield "LinkTables/AssignmentGroup.csv"


def dump_progsnap(zip_file, course_id, assignment_group_ids):
    yield generate_readme(zip_file)
    yield generate_metadata(zip_file)
    filename, code_states = generate_maintable(zip_file, course_id, assignment_group_ids)
    yield filename
    for code_base, code_state_id in tqdm(code_states.items()):
        for filename, contents in code_base:
            path = "CodeStates/{}/{}".format(code_state_id, filename)
            zip_file.writestr(path, contents)
    yield "CodeStates/*"
    yield generate_link_subjects(zip_file, course_id)
    for filename in generate_link_assignments(zip_file, course_id, assignment_group_ids):
        yield filename
    # LinkTables/
    #   Subject.csv + Roles
    #   CourseID
    #   AssignmentID
    #   AssignmentGroupID
    #   AssignmentGroupMembership
    #   Tags+Reviews
