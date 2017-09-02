"""
Author: Jeramey Tyler
email: tylerj2@rpi.edu
Date: June 2017

This code was written for use by the Rensselaer Polytechnic Institute's CS1 course. The intent is to parse a quiz
written in a pre-determined XML format into a series of HTML pages.
"""
import argparse
import os
import random
import shutil
import untangle


class QuizGenerator:
    """Generates an HTML quiz from an XML document.

    Generates a series of simple HTML pages displaying a quiz from a provided XML file.

    Attributes:
         source: A string indicating the source XML file.
         destination: A string indication the destination directory where the quiz will be generated.
         quiznum: An integer indication the quiz number or lecture number in the instance of CS1
         questions: An array of dictionaries representing the quiz questions. Each dictionary has a 'text' and a
            'response'.
         html: An array of strings representing the HTML pages to be written.
    """
    def __init__(self, s, d):
        """
        Init for the quiz generator.

        Generates a series of HTML pages for a quiz formatted in XML.
        //TODO: d requires the closing slash be provided on the string. Due to differences in how operating systems
            handle file paths. Thanks Microsoft.

        Args:
            s: A string indicating the source XML file.
            d: A string indicating the destination directory where the quiz will be generated.
        """
        self.source = s
        self.destination = d
        quiz = self.parse_quiz(s)

        self.quiznum = int(quiz['quiznum'])
        self.questions = quiz['questions']
        self.shuffle_questions(quiz['questions'])
        #//TODO: Add a home page that links to question one and vice versa. Add a sidebar to each page with links to
        # each question and answer.
        self.html = []

        for i in range(len(self.questions)):
            self.html.append(self.generate_html(self.questions[i], i+1))

        self.write_files()

    def parse_quiz(self, q):
        """
        Parses the XML file into a quiz dictionary.

        Parses a quiz from an XML file into a dictionary representation.

        Args:
            q: The path to the source XML file to generate the quiz.

        Returns:
            A dictionary representing the parsed quiz. Keys correspond to class attributes and values will be used to
                populate those class attributes.

             {'quiznum': 1,
             'questions':
                {'text':
                    [{'text': 'Question text',
                    'texttype': 'formula'}],
                'response':
                    [{'rtext': 'Response text',
                    'correct': 'incorrect",
                    'texttype': 'code'}]}}

        """
        q = untangle.parse(q).quiz

        quiz = dict()
        quiz['quiznum'] = q['quiznum']

        questions = []
        for qu in q.question:
            questions.append(self.parse_question(qu))
        quiz['questions'] = questions

        return quiz

    def parse_question(self, q):
        """
        Parses an XML question into a dictionary.

        Parses an untangle XML representation of a quiz question into a dictionary.

        Args:
            q: An untangle XML representation of a quiz question.

        Returns:
             A dictionary representation of a quiz question.

             {'text':
                {'text': 'Question text',
                'texttype': 'formula'},
             'responses':
                {'rtext': 'Response text',
                'correct': 'incorrect',
                'texttype': 'code'}}
        """
        responses = []
        texts = []

        # Text is processed the same regardless of whether it belongs to a question or a response.
        # Code blocks must be processed differently than formula or text blocks. This is necessary for to achieve the
        # line numbers and '|' at the beginning of lines of code.
        for response in q.response:
            if response['texttype'] == 'code':
                rtext = self.generate_code_block(response)
                responses.append({'rtext': rtext, 'correct': response['correct'], 'texttype': response['texttype']})
            else:
                responses.append({'rtext': response.cdata.strip(), 'correct': response['correct'], 'texttype': response['texttype']})
        # //TODO: Change key from 'text' to 'question'. Minor change but needed for terminology consistency.
        for text in q.text:
            if text['texttype'] == 'code':
                ctext = self.generate_code_block(text)
                texts.append({'text': ctext, 'texttype': text['texttype']})
            else:
                texts.append({'text': text.cdata.strip(), 'texttype': text['texttype']})

        question = dict()
        question['text'] = texts
        question['responses'] = responses
        return question

    def generate_html(self, q, qnum):
        """
        Generates HTML pages for a quiz question.

        Generates a question and an answer version HTML page for a quiz question. The question page will have
        links to their corresponding answer page and vice versa.

        Args:
            q: A dictionary representation of a quiz question.
            qnum: An integer indication the question number

        Returns:
            A tuple of strings representing The HTML of the question and answer versions of.

            ('<!DOCTYPE html><html><head></head><body>Question HTML</body>',
            '<!DOCTYPE html><html><head></head><body>Answer HTML</body>')
        """
        doc = """
            <!DOCTYPE html>
            <html>{head}{body}</html>
        """
        head = self.generate_head(qnum)
        body = self.generate_body()
        script = self.generate_script_html()
        
        doc = doc.format(**{'head': head, 'body': body})

        arrows = self.generate_arrows(qnum)
        question = self.generate_question_html(q)
        responses = self.generate_responses_html(q['responses'])

        params = dict()
        params['quiznum'] = self.quiznum
        params['questionnum'] = qnum
        params['head'] = head
        params['body'] = body
        params['script'] = script
        params['question'] = question

        # Question specific data
        if (qnum - 1) == 0:
            params['arrows'] = arrows['question']['right']
        else:
            params['arrows'] = arrows['question']['left'] + arrows['question']['right']
        params['ol'] = responses['question']

        question_html = doc.format(**params)

        # Answer specific data
        if qnum == len(self.questions):
            params['arrows'] = arrows['answer']['left']
        else:
            params['arrows'] = arrows['answer']['left'] + arrows['answer']['right']
        params['ol'] = responses['answer']

        answer_html = doc.format(**params)

        return question_html, answer_html

    def generate_head(self, qnum):
        """
        Generates the HTML head for a question.

        Args:
            qnum: An integer indication the question number

        Returns:
            A string representation of the HTML head tag for a question.
        """
        # I'm swapping a script alias for a script alias because the script contains JavaScript objects which causes
        # the format function to break. The script alias is the last alias swapped before the HTML is written to file.
        return """
        <head>
            <title>RPI CS1 Lecture {quiznum} Question {questionnum}</title>
            <link rel="stylesheet" type="text/css" href="style.css">
            {script}
        </head>
        """.format(**{'quiznum': self.quiznum, 'questionnum': qnum, 'script': '{script}'})

    def generate_body(self):
        """
        Generates the HTML body for a question.

        Returns:
            A string represention of the body of an HTML question.
        """
        return """
        <body>
        <div id="outer">
            <h1> Lecture {quiznum} </h1>
            <div id="inner">
                <h2> Question {questionnum} </h2>
                    {question}
                <br>
                    {ol}
                <br>
                    {arrows}
            </div>
        </div>
        </body>
        """

    def generate_arrows(self, questionnum):
        """
        Generates the HTML Prev and Next buttons.

        Generates a Prev and Next button for a page for a provided question number. Returns a Prev and Next button for
        each page with no check for necessity.

        Args:
            questionnum: An integer representing the question number

        Returns:
            A dictionary representing the Prev and Next buttons for both the question and answer versions of a page.

            {'question':
                {'left': '<div id="leftarrow" class="button"><a href=""><span>&larr;Prev</span></a></div>',
                'right': '<div id="rightarrow" class="button"><a href=""><span>Next&rarr;</span></a></div>'},
            'answer':
                {'left': '<div id="leftarrow" class="button"><a href=""><span>&larr;Prev</span></a></div>',
                'right': '<div id="rightarrow" class="button"><a href=""><span>Next&rarr;</span></a></div>'}}
        """
        # //TODO: Change terminology to prevarrow/nextarrow for consistency
        left_arrow = '<div id="leftarrow" class="button"><a href="{}"><span>&larr;Prev</span></a></div>'
        right_arrow = '<div id="rightarrow" class="button"><a href="{}"><span>Next&rarr;</span></a></div>'
        # //TODO: Parameterize file name prefix and let users optionally provide it.
        link = 'lecture{:02d}_question{:02d}_{}.html'

        arrows = dict(question={}, answer={})
        arrows['question']['left'] = left_arrow.format(link.format(self.quiznum, questionnum - 1, 'a'))
        arrows['question']['right'] = right_arrow.format(link.format(self.quiznum, questionnum, 'a'))

        arrows['answer']['left'] = left_arrow.format(link.format(self.quiznum, questionnum, 'q'))
        arrows['answer']['right'] = right_arrow.format(link.format(self.quiznum, questionnum + 1, 'q'))

        return arrows

    # //TODO: Since I'm including a script tag later question and answer versions can be handled by a single page and a
    # little jquery.
    def generate_question_html(self, q):
        """
        Generates the HTML block for a question.

        For questions whose texttype is equal to 'text' or 'formula' use this function. The text size of the questions
        is set here, lazily, by wrapping a div in an h3.

        Args:
            q: The dictionary representation of a quiz question.

        Returns:
            A string representation of the question's text.

            <h3><div id="question">
                <div class="formula">Solve for x: \(y = mx + b\)</div>
            </div></h3>
        """
        # //TODO: Remove h3 and style properly
        div = """<h3><div id="question">
                {}
            </div></h3>"""
        span = '<div class="{}">{}</div>'
        text = ''

        for t in q['text']:
            text += span.format(t['texttype'], t['text'])

        return div.format(text)

    def generate_responses_html(self, rs):
        """
        Generates the HTML block for a set of responses.

        Generates both a question and an answer version of the responses. The question and answer version differ only
        by the inclusion of the correct/incorrect CSS classes in the answer version.

        Args:
            rs: An array dictionaries representing a question's responses.

        Returns:
            A dictionary of strings representing the question and answer HTML.

            {'question': '<h3><div id="responses">...</div></h3>',
             'answer': '<h3><div id="responses">...</div></h3>',}
        """
        # //TODO: Here and other places I'm returning a dictionary but in generate_html I'm returning a similarly
        # structured tuple. For consistency make them match. Dictionary is preferable for maintainability/readability.
        ol = """<h3><div id="responses">
                <ol type="a">
                    {}
                </ol>
            </div></h3>"""
        li = '<li class="{class}"><span class="{texttype}">{rtext}</span></li>\n'
        q = ''
        a = ''

        for r in rs:
            q += li.format(**{'class': '', 'texttype': r['texttype'], 'rtext': r['rtext']})
            a += li.format(**{'class': r['correct'], 'texttype': r['texttype'], 'rtext': r['rtext']})
        return {'question': ol.format(q), 'answer': ol.format(a)}

    def generate_script_html(self):
        """
        Generates the HTML script tag.

        This string is difficult to parse and tends to break str.format().

        Currently this is only necessary in order to render LaTex equations. LaTex configurations are handled by
        MathJax and can be edited in the MathJax.Hub.Config. The MathJax version is hardcoded, if future issues arise
        with LaTex generation check there first.

        Returns:
            A string representation of the HTML script tag. This needs to be inserted into the head.
        """
        return """<!-- Needed to render LaTex -->
            <script type="text/x-mathjax-config">
                MathJax.Hub.Config({
                    jax: ["input/TeX", "output/CommonHTML"],
                    extensions: ["tex2jax.js"],
                    tex2jax: {
                        inlineMath: [["\\\(","\\\)"]],
                        displayMath: [['$$', '$$'], ["\\\[", "\\\]"]],
                        processEscapes: true,
                        processEnvironments: false
                    }
                });
            </script>
            <script type="text/javascript"
                src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
            </script>"""

    def shuffle_questions(self, qs):
        """
        Shuffles the ordering of the questions and their responses

        Performs an inplace shuffling of each question's responses then performs an in place shuffle of the questions.

        Args:
            qs: An array of dictionary representations of quiz questions.

        Returns:
            An array of dictionary representations of quiz questions.
        """
        for i in range(len(qs)):
            random.shuffle(qs[i]['responses'])
        random.shuffle(qs)

    def write_files(self):
        """
        Writes the HTML files to disk.

        Writes both the question and answer versions of each quiz question. Pages are numbered sequentially and
        question and answer versions are indicated by either a q or an a suffix on the file name.
        """
        f = 'lecture{:02d}_question{:02d}_{}.html'

        if not os.path.isdir(self.destination):
            os.mkdir(self.destination)

        for i in range(len(self.html)):
            with open(self.destination + f.format(self.quiznum, i + 1, 'q'), 'w') as file:
                file.write(self.html[i][0])
                file.close()

            with open(self.destination + f.format(self.quiznum, i + 1, 'a'), 'w') as file:
                file.write(self.html[i][1])
                file.close

        shutil.copy('style.css', self.destination)

    def generate_code_block(self, code):
        """
        Generates HTML code blocks.

        Code needs to be styled a little differently in order to style it. A <pre> is necessary to keep the
        formatting on the text without having to serialize HTML characters for whitespace and newline etc.. Line
        numbers are handled by CSS counters which increment for <code> children in the <pre>.
        :param code:
        :return:
        """
        pre = '<pre class="code" style="counter-reset: line {}">{}</pre>'
        code_tags = """<code>{}\n</code>"""
        c = ''

        for line in code.code:
            c += code_tags.format(line.cdata)

        return pre.format(code['startline'], c)
    # //TODO: Validate XML against XSD (first create XSD)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="The source xml file containing the quiz.")
    parser.add_argument("-d", "--destination", help="The destination directory for the html files that"
                                                    " will be generated.")
    args = parser.parse_args()
    s = args.source
    d = args.destination

    QuizGenerator(s, d)
