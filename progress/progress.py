"""
High level proposal:
- course is a tree or DAG of usage_ids.
- each leaf has a checker (may be the null checker for non-checked things)
- each interior node has an aggregator
- Checkers report scores to the progress service
- progress service uses aggregators to report scores for any node in the tree.
   - implementation note: if clever, can update things lazily and cache to avoid doing too
     much work.

- Which progress aggregators are used at each node and how they're configured is a
  separate authoring problem.  Presumably this could live in the metadata for the block.

Q:

 - how do I record the grade for an outside-of-the-online-class course element?
   Give it a placeholder block with an id.

 - do aggregate Xblocks do any of their own grading?  e.g. does a vertical decide how to
   aggregate grades within it?  Or is there a separate ProgressAggregator attached to each
   node?  Or is there logically a single ProgressAggregator for the course?
   - There is a ProgressAggregator attached to each node.  They may be written by xblock
     authors, but are separate objects.

 - separate out per-element and aggregate?

 - how about the course gets to specify a progress service to use, and we just display it?
   The config + implementation for the service defines the grading policy.  I like it.
   But, it means that the course structure is both in the xblock def and used by the
   progress service.


 - where do things like late days, extensions, penalties, etc go?

   Stories:
      - need to be able to display progress for subsections
      - need to be able to display local and global grading policy for a course
      - need to record more than just a number for progress.  E.g. rubric data, comments,
        etc.  Does that live in this service?
      - some people want non-numeric progress.  Still need some aggregation function?
      - should we be able to get an explanation of how the grade for any node was computed
        out?

      - different students may see different things (e.g. randomization between problems,
        general A/B testing, adaptive display, etc).  This means they have different
        grading requirements.  If LMS + grading side of things in general only sees the
        per-student version of the course, this may all just work.
"""


"""
Adaptive courseware thought experiment:

My_Course
  - Week1
     - pre_test_problems (regular sequence of stuff)
  - Week2
     - intro
     - adaptive_sequence
        - if_beginner  (10 points)
        - if_intermediate (8 points)
        - if_expert (24 points)

Student will only see 1 of the 3 adaptive questions.  How should this work?

- GradeAggregator for adaptive_sequence needs access to what was chosen, should be aware
  of how adaptive sequences work, do the right thing.
  - person writing the adaptive sequence block needs to also write the adaptive sequence
    grade aggregator.
"""

"""
Diff between course structure and what instructor wants to treat as an exam...

My_course
  - Week1
     - intro, sample_problem, ps1_problem1
     - some_more_stuff, ps1_problem2, ps1_problem3
     - ps2_problem1
  - Week2
     - ps2_problem2, example, ps2_problem3
     ...

So ps1 is split between multiple sequences, ps2 split between multiple weeks.

Argues for grade aggregators that look at an arbitrary set of blocks.  Grading policy
structure doesn't necessarily have to match course structure.  I think that leaving this
out for now is ok.  One way to handle it is to have get_progress() take things besides
usage_ids.  Another is to use the fact that we can have a DAG in the course structure and
create a separate PS2 block that has the appropriate things as its children, and give it
the right aggregation function.  I kind of like the simplicity of that...
"""


class ProgressService(object):
    """
    Record progress for leaf nodes of course, and aggregates it at all levels.
    """

    def __init__(self, modulestore, user_service, aggregator_config):
        """
        Here to specify dependencies.  Exactly how it gets this info is implementation
        dependent, but a progress store will need access to:
            - course structure, per user if there are per-user customizations.

            - the set of possible users (maybe?  could just treat any user id as valid and
              store data)

            - what aggregators to use at each nodes.  Maybe this comes from metadata
              attached to course structure, maybe not.

        """
        pass

    @authrequired
    def record_progress(self, user_id, usage_id, submission_id,
                        score, max_score, message, data):
        """
        user_id:
           duh
        usage_id:
            Which block is this the score for.  Blocks should report their own progress,
            not the aggregate progress of their children (so a sequence that doesn't have
            its own assessment shouldn't record progress)
        submission_id:
            The particular submission this corresponds to.  The user may answer the same
            question many times, and we may want to distinguish these.
        score:
            float, non-negative. May be None if N/A.  May be larger than max_score
            (e.g. with extra credit)
        max_score:
            float, positive.  Maximum score possible on the problem.  May be None.
        message:
            string. A message to display to the student.  May include HTML.  May be None.
        data:
            Json string.  Extra stuff to store.  Intended for things like detailed notes
            on rubric, any peer feedback, etc, stored in a machine readable format.

        Returns nothing.

        Raises
            NoSuchUser
            NoSuchUsage
            ProgressGoBoom if there was a problem saving the data.
        """
        pass

    @authrequired
    def get_progress(self, user_id, usage_id):
        """
        Return the progress for a user on a particular usage.

        MAY return a score even though this usage_id has never been recorded for this
        user, for example if it can be computed from available scores.

        Returns
           None if no progress available.
           (score, max_score, message, data) otherwise.

        Raises
           NoSuchUser
           NoSuchUsage
           ProgressGoBoom if there was a problem loading the data

        """
        if recorded:
            return
        else:
            aggregator = get_aggregator(usage_id)
            child_grades = [get_progress(child)
                            for child in children(usage_id)]
            # TODO: cache
            return aggregator.aggregate(user_id, usage_id)

    def _maybe__notify_me(self, user_id, usage_id, callback):
        """
        Tell me when something changes...
        user_id None means all.
        usage_id None means all.
           May need to be able to filter by parts of usage_id (e.g. course_id).
        callback.  Call with some details...

        MUST notify when grade changes either because of an explicit update or a change in
        a dependencies' value.
        """
        pass


class GradeAggregator(object):
    """
    A service that knows how to aggregate a bunch of descendent (just child?) grades into
    a single grade.

    Q:
    - Does a grade aggregator need the actual responses for the questions its responsible
      for, or will just the grades with metadata suffice?

    - Does it need data for just its children or all its descendants?  The former
      would be nice if we think that's sufficient.

    - Do we really need a separate notion of checker and grader?  Perhaps it is
      useful--checkers check things.  Graders are really GradeAggregators that aggregate
      things.  In particular, they may aggregate things that aren't problems in the usual
      sense.  E.g. there may be a 'checker' for how good your forum posts are.  It can be
      plugged in to a GradeAggregator like a regular problem.

    """
    def aggregate(user_id, usage_id, child_grades):
        """
        Aggregate the grades for the children of usage_id into a grade for usage_id.

        user_id: duh
        usage_id: the block whose grade we want
        child_grades: the grades for the children of usage_id (details?)

        Returns
            grade details for this usage
        """
        # Can just average, add up, drop things, etc.
        pass


class StudentResponseStore(object):
    """
    I think this is separate from a progress service.

    The StudentResponseStore's mission:

    Store all the different responses student give to problems (all versions).
    Track submission times.
    Compute distributions of answers per problem.
    Compute distributions of attempts per problem.
    Track problem versions, random seeds used to be able to recreate exactly what the
      student saw when they answered?
    """
    pass


class StudentResponse(object):
    """
    Input from student.
    Details about grading from problem--right answer, etc.
    """
    pass


class Checker(object):
    """
    A service that knows how to grade certain types of problems.
    """
    def check(student_response):
        """
        Return score, hint, msg, extra data.
        """
        pass




class SampleProgressClients(object):
    """
    Some sample client functions that _should_ be easy to write.

    Note that some of these are likely going to want to interact with a GradingPolicy
    interface, not a ProgressService.
    """

    def get_progress_for_problem(user_id, usage_id):
        pass

    def get_progress_for_course(user_id):
        pass

    def get_gradebook(course_id):
        """Get all the grades for everyone.  Current a performance issue."""
        pass

    def set_grading_policy(course_id, ???):
        pass

    def set_problem_as_extra_credit(course_id, usage_id, points):
        pass

    def record_grade_for_problem(user_id, usage_id, grade):
        pass

    def record_grade_for_offline_task(user_id, some_id, grade):
        pass

    def record_grade_with_notes(user_id, usage_id, grade, notes):
        pass

    def record_grade_with_notes_and_other(user_id, usage_id, grade, notes, extra_data):
        pass

    def give_batman_an_extension(usage_id, batman_id, extension_length):
        pass


    def get_updated_grade_after_adding_a_problem(course_id, user_id):
        pass

    def get_grade_before_deciding_which_followup_problem_to_show(course_id, user_id):
        pass


    def see_grade_history(user_id, usage_id):
        """
        Presumably the returned history needs to match up with specific versions of the
        problem and the submission, so if this is supported by this interface, we'll need
        to keep track of that when recording grades in the first place.
        """
        pass

    def get_progress_for_week(week_usage_id, user_id):
        """
        Return some notion of progress--scores, how much attempted, etc.  Distinguish
        between 'I tried and got 0' and 'have not tried yet'...
        """
        pass


    def explain_course_grading_policy_to_student(course_id, user_id):
        """
        Get and display details on out how the grade was computed...
        """
        pass
