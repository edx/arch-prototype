"""
Q:

 - how do I record the grade for an outside element?  Give it a placeholder with an id?

 - do aggregate Xblocks do any of their own grading?  e.g. does a vertical decide how to
   aggregate grades within it?  Or is there a separate ProgressAggregator attached to each
   node?  Or is there logically a single ProgressAggregator for the course?

 - separate out per-element and aggregate?

 - how about the course gets to specify a progress service to use, and we just display it?
   The config + implementation for the service defines the grading policy.  I like it.
   But, it means that the course structure is both in the xblock def and used by the
   progress service.

   Stories:
      - need to be able to display progress for subsections
      - need to be able to display local and global grading policy for a course
      - need to record more than just a number for progress.  E.g. rubric data, comments,
        etc.  Does that live in this service?
      - some people want non-numeric progress.  Still need some aggregation function?
      - should we be able to get an explanation of how the grade for any node was computed
        out?

"""

class ProgressService(object):
    """
    Stores progress.
    """

    def record_progress(self, user_id, usage_id, value):
        """
        What is the type of value?

        If usage_id is one for which the ProgressService normally computes the value.
        """
        pass

    def get_progress(self, user_id, usage_id):
        """
        Return None if unavailable.

        MAY return a score even though this usage_id has never been recorded for this
        user, for example if it can be computed from available scores.
        """
        pass

    def notify_me(self, user_id, usage_id):
        """
        Tell me when something changes...
        user_id None means all.
        usage_id None means all.
           May need to be able to filter by parts of usage_id (e.g. course_id).

        MUST notify when grade changes either because of an explicit update or a change in
        a dependencies' value.
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

    def see_grade_history(user_id, usage_id):
        """
        Presumably the returned history needs to match up with specific versions of the
        problem and the submission, so if this is supported by this interface, we'll need
        to keep track of that when recording grades in the first place.
        """
        pass

    
