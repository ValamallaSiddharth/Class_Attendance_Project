function Services() {
  const services = [
    {
      title: "Web Design",
      description: "Beautiful and responsive website designs.",
    },
    {
      title: "React Development",
      description: "Fast frontend development using React components.",
    },
    {
      title: "Project Support",
      description: "Perfect structure for college and client projects.",
    },
  ];

  return (
    <section className="section" id="services">
      <h2>Our Services</h2>

      <div className="service-grid">
        {services.map((service, index) => (
          <div className="service-card" key={index}>
            <h3>{service.title}</h3>
            <p>{service.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default Services;