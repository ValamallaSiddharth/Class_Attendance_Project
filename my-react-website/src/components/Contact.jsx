function Contact() {
  return (
    <section className="section contact" id="contact">
      <h2>Contact Us</h2>
      <p>Have a project idea? Contact us and let’s build something amazing.</p>

      <form className="contact-form">
        <input type="text" placeholder="Enter your name" />
        <input type="email" placeholder="Enter your email" />
        <textarea placeholder="Enter your message"></textarea>
        <button type="submit">Send Message</button>
      </form>
    </section>
  );
}

export default Contact;