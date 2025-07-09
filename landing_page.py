# landing_page.py

from dash import dcc, html
import dash_bootstrap_components as dbc
from flask_login import current_user
import design_components as dc

def create_public_navbar():
    """Creates the navbar for all public-facing pages (for non-logged-in users)."""
    nav_items = [
        dbc.NavItem(dbc.NavLink("Coming Soon", href="/coming-soon")),
        dbc.NavItem(dbc.NavLink("About", href="/about")),
        dbc.NavItem(dbc.NavLink("Register", href="/register")),
        dbc.NavItem(dbc.NavLink("Log In", href="/login")),
    ]
    
    return dbc.NavbarSimple(
        children=nav_items,
        brand=html.Img(src='/assets/riskwatch-logo.png', alt="Risk Watch Logo", className="landing-logo-img", style={'height': '55px'}),
        brand_href="/",
        color="transparent",
        dark=False,
        fluid=True,
        className="landing-header"
    )

def create_hero_content():
    """
    Creates ONLY the hero content of the landing page.
    This is now a reusable component for both logged-in and public views.
    """
    return html.Main(className="hero-section", children=[
        html.Div(className="hero-left", children=[
        html.H1([
        html.Span("Ditch the Clipboard. Drive Compliance.", style={'fontWeight': 'bold','fontSize': 'clamp(40px, 3vw, 36px)', 'marginBottom': '10px'}),
        html.Br(),
        " True operational resilience comes from proactively managing risk across every function. RiskWatch is the intelligent platform designed for the complexities of modern HSSE. We provide the tools to move beyond reactive paperwork, helping you identify hazards, secure assets, and maintain environmental compliance all from one place. Turn your HSSE program into a strategic advantage."
        ], className="hero-headline")
        ]),
    ])

def build_full_public_landing_page():
    """
    Assembles the complete landing page for non-authenticated users,
    including the public navbar, hero content, and footer.
    Uses Bootstrap flex classes to ensure the footer is always at the bottom.
    """
    return html.Div([
        create_public_navbar(),
        # Wrap hero content in a div that can grow to fill space
        html.Div(create_hero_content(), className="flex-grow-1 d-flex align-items-center"),
        dc.create_footer()
    ], className="d-flex flex-column min-vh-100")


def create_public_layout(content):
    """
    A wrapper for all public static pages (About, Privacy, etc.).
    Provides the public navbar, a container for content, and the footer.
    Uses Bootstrap flex classes to ensure the footer is always at the bottom.
    """
    return html.Div([
        create_public_navbar(),
        dbc.Container(content, fluid=False, className="py-5 flex-grow-1"),
        dc.create_footer()
    ], className="d-flex flex-column min-vh-100")

def create_about_page():
    return html.Div(className="about-content", children=[
        html.H1("About Risk Watch"),
        html.P("Risk Watch is a next-generation safety management platform designed to empower HSE professionals. By leveraging artificial intelligence, we streamline the process of safety observations, risk assessment, and reporting, turning raw data into actionable insights instantly."),
        html.P("Our mission is to create safer workplaces by making safety management intuitive, efficient, and data-driven. We believe that technology can significantly reduce administrative burden, allowing safety professionals to focus on what truly matters: preventing incidents and protecting people.")
    ])

def create_privacy_page():
    return html.Div(className="legal-content", children=[
        html.H1("Privacy Policy"),
        html.P("Last Updated: June 8, 2025", className="legal-last-updated"),
        html.P("Your privacy is important to us. It is Risk Watch's policy to respect your privacy regarding any information we may collect from you across our website and other sites we own and operate."),
        html.P("We only ask for personal information when we truly need it to provide a service to you. We collect it by fair and lawful means, with your knowledge and consent. We also let you know why we’re collecting it and how it will be used."),
        html.P("If you have any questions about this Privacy Policy, please contact us at: arjunmenon888@gmail.com."),
    ])

def create_terms_page():
    return html.Div(className="legal-content", children=[
        html.H1("Terms of Use for Risk Watch"),
        html.P("Last Updated: June 8, 2025", className="legal-last-updated"),
        html.H2("1. Acceptance of Terms"),
        html.P("By accessing and using the Risk Watch application ('Service'), you accept and agree to be bound by the terms and provision of this agreement. In addition, when using these particular services, you shall be subject to any posted guidelines or rules applicable to such services."),
        html.H2("2. User Conduct"),
        html.P("As a condition of use, you promise not to use the Service for any purpose that is unlawful or prohibited by these Terms.")
    ])
    
def create_coming_soon_page():
    features = [
        "Incident & Near-Miss Reporting", "Risk Assessments (JSA / HIRA)", "Inspection Checklists",
        "Corrective & Preventive Action Tracker (CAPA)", "Training & Competency Management",
        "Permit to Work (PTW) System", "Legal Compliance Register", "Emergency Drill Logs",
        "Environmental Monitoring Logs", "Behavior-Based Safety (BBS)", "Dashboard & Analytics",
        "PDF Report Export", "User Role Management", "Heat Map by Risk Level"
    ]
    return html.Div(className="features-list-content", children=[
        html.H1("Coming Soon: New Features"),
        html.P("We are constantly working to enhance Risk Watch with powerful new tools to streamline your safety management processes. Here's a preview of what's on our roadmap:"),
        html.Ul(className="features-list", children=[html.Li(feature) for feature in features])
    ])

def register_callbacks(app):
    """Registers callbacks for the landing page."""
    pass